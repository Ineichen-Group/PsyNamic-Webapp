import os
import logging
import math
import numpy as np
from ast import literal_eval
import pandas as pd
import torch
import json
import torch.nn.functional as F
from torch.utils.data import Dataset
from datetime import datetime
import re
from data.helper import check_if_pred_exist, cleanup_old_logs, format_timedelta_hms
import argparse
import sys

# Assuming Trainer, DataSplit, DataSplitBIO are defined elsewhere in your project
from typing import Union
from transformers import Trainer, AutoModelForTokenClassification, AutoModelForSequenceClassification, AutoTokenizer

import pytz
import pandas as pd
from torch.utils.data import Dataset

zurich = pytz.timezone('Europe/Zurich')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# TODO: A little redundant with pipeline/train.py's Dataset, consider refactoring


class SimpleDataset(Dataset):
    """Dataset for prediction with BERT for Classification or NER."""

    ID_COL = 'id'
    TEXT_COL = 'text'

    def __init__(self, csv_file: Union[str, pd.DataFrame], tokenizer, max_len=512, multilabel=False, is_ner=False):
        if isinstance(csv_file, str):
            self.df = pd.read_csv(csv_file)
        else:
            self.df = csv_file
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.is_multilabel = multilabel
        self.is_ner = is_ner

        # Check if pubmed_id exists, else use 'id'
        if self.ID_COL not in self.df.columns:
            self.ID_COL = 'pubmed_id'

        if self.is_ner:
            self.chunks = self._build_ner_chunks()

    def _build_ner_chunks(self):
        chunked_rows: list[dict[str, any]] = []

        for _, row in self.df.iterrows():
            id_ = row[self.ID_COL]
            text = row[self.TEXT_COL]

            # Tokenize with offsets to get word_ids
            encoding = self.tokenizer(
                text,
                return_attention_mask=False,
                return_token_type_ids=False,
                return_offsets_mapping=True,
                truncation=False
            )

            tokens = self.tokenizer.convert_ids_to_tokens(
                encoding["input_ids"])
            word_ids = encoding.word_ids()

            # Chunking
            if len(tokens) <= self.max_len:
                chunked_rows.append({
                    self.ID_COL: id_,
                    self.TEXT_COL: text,
                    'tokens': tokens,
                    'word_ids': word_ids,
                    'chunk_idx': 0
                })
            else:
                num_chunks = math.ceil(len(tokens) / self.max_len)
                for i in range(num_chunks):
                    start = i * self.max_len
                    end = start + self.max_len
                    chunked_rows.append({
                        self.ID_COL: id_,
                        self.TEXT_COL: text,
                        'tokens': tokens[start:end],
                        'word_ids': word_ids[start:end],
                        'chunk_idx': i
                    })

        return pd.DataFrame(chunked_rows)

    def __len__(self):
        if self.is_ner:
            return len(self.chunks)
        return len(self.df)

    def __getitem__(self, idx):
        if self.is_ner:
            row = self.chunks.iloc[idx]
            tokens = row['tokens']
            dummy_label = [-100] * len(tokens)

            return {
                'id': row[self.ID_COL],
                'text': row[self.TEXT_COL],
                'tokens': tokens,
                'labels': dummy_label,
                'chunk_idx': row['chunk_idx'],
                'word_ids': row['word_ids']
            }

        else:
            row = self.df.iloc[idx]
            id_ = row[self.ID_COL]
            text = row[self.TEXT_COL]

            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=self.max_len,
                return_tensors='pt'
            )

            return {
                'id': id_,
                'text': text,
                **{key: val.squeeze(0) for key, val in encoding.items()}
            }


def predict(model: Union[AutoModelForTokenClassification, AutoModelForSequenceClassification], test_dataset: SimpleDataset, threshold: float = 0.5, batch_size: int = 1) -> pd.DataFrame:
    """
    Predicts the labels for the test dataset and saves predictions to a CSV.
    Works for classification and token-level NER using a SimpleDataset.
    """

    # Ensure threshold is a float
    threshold = float(threshold) if threshold else None
    pred_data = []

    device = next(model.parameters()).device
    model.eval()

    # ---------- NER PREDICTION ----------
    if test_dataset.is_ner:
        all_logits = []
        all_probs = []

        total_chunks = len(test_dataset)
        report_interval = max(1, total_chunks // 100)

        pad_id = test_dataset.tokenizer.pad_token_id
        if pad_id is None:
            pad_id = test_dataset.tokenizer.eos_token_id or 0

        # Run inference in batches of chunks
        for start in range(0, total_chunks, batch_size):
            end = min(start + batch_size, total_chunks)
            batch_samples = [test_dataset[i] for i in range(start, end)]

            # Convert token lists to ids and pad to same length
            id_seqs = [test_dataset.tokenizer.convert_tokens_to_ids(s["tokens"]) for s in batch_samples]
            lengths = [len(seq) for seq in id_seqs]
            max_len = max(lengths)

            padded = [seq + [pad_id] * (max_len - len(seq)) for seq in id_seqs]
            input_ids = torch.tensor(padded, device=device)
            attention_mask = (input_ids != pad_id).long().to(device)

            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits_batch = outputs.logits  # (batch, seq_len, num_labels)
                probs_batch = torch.softmax(logits_batch, dim=-1)

            # Split batch outputs back per chunk, trimming padding
            for i_in_batch, seq_len in enumerate(lengths):
                logits = logits_batch[i_in_batch][:seq_len]
                probs = probs_batch[i_in_batch][:seq_len]
                all_logits.append(logits.cpu().numpy())
                all_probs.append(probs.cpu().numpy())

            # Progress logging at ~10% intervals
            if (end) % report_interval == 0 or end == total_chunks:
                logging.info(
                    f"\tNER progress: {end}/{total_chunks} ({int(end/total_chunks*100)}%)")

        # Convert to numpy arrays
        pred_labels_idx = [np.argmax(p, axis=-1) for p in all_probs]

        # Now MERGE CHUNKS PROPERLY
        for sample_id, group in test_dataset.chunks.groupby(test_dataset.ID_COL):

            group = group.sort_values("chunk_idx")

            merged_tokens = []
            merged_labels = []
            merged_probs = []

            for chunk_row_idx in group.index:
                tokens = test_dataset.chunks.loc[chunk_row_idx, "tokens"]
                word_ids = test_dataset.chunks.loc[chunk_row_idx, "word_ids"]

                preds_chunk = pred_labels_idx[chunk_row_idx]
                probs_chunk = all_probs[chunk_row_idx]

                current_word_tokens = []
                current_word_label = None
                current_word_prob = None
                current_word_id = None

                for j, (token, word_id) in enumerate(zip(tokens, word_ids)):

                    if word_id is None:
                        continue

                    # New word starts
                    if word_id != current_word_id:
                        # Save previous word
                        if current_word_tokens:
                            word = test_dataset.tokenizer.convert_tokens_to_string(
                                current_word_tokens)
                            merged_tokens.append(word)
                            merged_labels.append(current_word_label)
                            merged_probs.append(current_word_prob)

                        # Start new word
                        current_word_tokens = [token]
                        # first subtoken label
                        current_word_label = int(preds_chunk[j])
                        current_word_prob = float(probs_chunk[j].max())
                        current_word_id = word_id

                    else:
                        current_word_tokens.append(token)

                # Save last word
                if current_word_tokens:
                    word = test_dataset.tokenizer.convert_tokens_to_string(
                        current_word_tokens)
                    merged_tokens.append(word)
                    merged_labels.append(current_word_label)
                    merged_probs.append(current_word_prob)

            pred_data.append({
                "id": sample_id,
                "text": group.iloc[0][test_dataset.TEXT_COL],
                "tokens": merged_tokens,
                "pred_labels": merged_labels,
                "probabilities": merged_probs
            })


    # ---------- CLASSIFICATION PREDICTION ----------
    else:
        probs = []
        preds = []

        total_samples = len(test_dataset)
        report_interval = max(1, total_samples // 100)

        # Process in batches of texts
        for start in range(0, total_samples, batch_size):
            end = min(start + batch_size, total_samples)
            batch_texts = [test_dataset[i]["text"] for i in range(start, end)]

            encoding = test_dataset.tokenizer(
                batch_texts,
                return_tensors="pt",
                truncation=True,
                max_length=test_dataset.max_len,
                padding=True
            )

            input_ids = encoding["input_ids"].to(device)
            attention_mask = encoding["attention_mask"].to(device)

            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits_batch = outputs.logits  # (batch, num_labels) or (batch, seq_len, num_labels)

            # If sequence classification returns seq_len dim, squeeze
            if logits_batch.dim() == 3:
                logits_batch = logits_batch.squeeze(1)

            for i_in_batch in range(logits_batch.shape[0]):
                logits = logits_batch[i_in_batch]

                if test_dataset.is_multilabel:
                    probs_tensor = torch.sigmoid(logits)
                    pred_indices = (probs_tensor >= threshold).nonzero(as_tuple=False).squeeze().tolist()
                    if not isinstance(pred_indices, list):
                        pred_indices = [pred_indices]
                    pred_probs = [probs_tensor[i].item() for i in pred_indices]
                    probs.append(pred_probs)
                    preds.append(pred_indices)
                else:
                    prob = torch.softmax(logits, dim=-1)
                    pred = int(torch.argmax(prob).item())
                    probs.append(prob.tolist())
                    preds.append(pred)

            # Progress logging at ~10% intervals
            if (end) % report_interval == 0 or end == total_samples:
                logging.info(
                    f"\tClassification progress: {end}/{total_samples} ({int(end/total_samples*100)}%)")

        for i in range(len(test_dataset)):
            sample = test_dataset[i]

            pred_data.append({
                "id": sample["id"],
                "text": sample["text"],
                "prediction": preds[i],
                "probability": probs[i]
            })

    return pd.DataFrame(pred_data)


def load_model(model_path: str, task: str):
    """
    Load a fine-tuned BERT model and tokenizer from a save directory.
    Returns the model and tokenizer. Trainer is optional for inference.
    """
    model_path = os.path.join(SCRIPT_DIR, model_path)
    # For prediction on a laptop, CPU is usually safest
    device = torch.device("cpu")

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    if "ner" in task.lower():
        model = AutoModelForTokenClassification.from_pretrained(model_path)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(model_path)

    model.to(device)
    model.eval()

    return model, tokenizer


def get_latest_data(data_dir: str) -> str:
    """Get latest csv from data directory by finding the newest YYYYMMDD
    date token in filenames (e.g. pubmed_results_19000101_20260530_00-03-43.csv).
    Falls back to file modification time if no date token is found.
    """

    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the specified directory.")

    date_re = re.compile(r"(\d{8})")

    def file_latest_date(fname: str):
        # find all 8-digit date-like tokens and parse them
        matches = date_re.findall(fname)

        # Prefer the second token when available (filename is from_date_to_date)
        preferred_idx = 1 if len(matches) >= 2 else 0

        if matches:
            # Try preferred index first
            try:
                return datetime.strptime(matches[preferred_idx], "%Y%m%d")
            except Exception:
                # Fall back to any other parsable token (reverse order to prefer later dates)
                for tok in reversed(matches):
                    try:
                        return datetime.strptime(tok, "%Y%m%d")
                    except Exception:
                        continue

        # fallback: use file modification time
        try:
            mtime = os.path.getmtime(os.path.join(data_dir, fname))
            return datetime.fromtimestamp(mtime)
        except Exception:
            return datetime.min

    latest_file = max(csv_files, key=file_latest_date)
    return os.path.join(data_dir, latest_file)


def extract_retrieval_date_from_filename(filename: str) -> str:
    """pubmed_results_20231216_20260112_00:00:10.csv -> 20260112"""
    base_name = os.path.basename(filename)
    parts = base_name.split('_')
    try:
        return parts[-2]
    except:
        return "unknown_date"


def main():

    parser = argparse.ArgumentParser(description="Run prediction pipeline")
    parser.add_argument(
        '-i', '--input_file',
        type=str,
        help='Path to the input CSV file for prediction. If not provided, the latest file from the data directory will be used.'
    )
    parser.add_argument(
        '-o', '--output_dir',
        type=str, default='data/predictions',
        help='Directory to save prediction outputs. Default is data/predictions.'
    )
    parser.add_argument(
        '--skip_relevance',
        action='store_true',
        help='Skip relevance prediction step.'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1,
        help='Batch size for model inference (default: 1)'
    )
    parser.add_argument(
        '--log-to-stdout',
        action='store_true',
        help='Redirect logs to stdout instead of a logfile.'
    )
    log_dir = os.path.join(SCRIPT_DIR, 'log')
    os.makedirs(log_dir, exist_ok=True)

    default_log_file = os.path.join(
        log_dir,
        f'predict_{datetime.now(zurich).strftime("%Y%m%d_%H%M%S")}.log'
    )
    parser.add_argument(
        '-l', '--log-file',
        type=str,
        default=default_log_file,
        help='Path to logfile (defaults to SCRIPT_DIR/log).'
    )

    args = parser.parse_args()

    log_dir = os.path.join(SCRIPT_DIR, 'log')
    os.makedirs(log_dir, exist_ok=True)
    cleanup_old_logs(log_dir)

    # Configure logging: either to stdout (useful in container/stdout-first setups)
    # or to the logfile path provided by `--log-file`.
    if getattr(args, 'log_to_stdout', False):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True,
        )
    else:
        logging.basicConfig(
            filename=args.log_file,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            force=True
        )

    logging.info('Prediction process started.')
    PUBMED_DATA_DIR = 'data/pubmed_fetch_results'
    MODEL_INFO = 'pipeline/model_paths.json'
    FINAL_PRED = args.output_dir
    RELEVANT_STUDIES = 'data/relevant_studies'

    try:
        # Get latest pubmed data file
        if args.input_file:
            csv_file = args.input_file
            logging.info(f'Using provided input file: {csv_file}')
            retrieval_date = extract_retrieval_date_from_filename(csv_file)
        else:
            csv_file = get_latest_data(PUBMED_DATA_DIR)
            logging.info(f'Loaded latest data file: {csv_file}')
            retrieval_date = extract_retrieval_date_from_filename(csv_file)

        with open(MODEL_INFO, 'r', encoding='utf-8') as file:
            model_info = json.load(file)
        logging.info(f'Loaded models info from {MODEL_INFO}')

        rel_pred = check_if_pred_exist(RELEVANT_STUDIES, retrieval_date)
        # Case 1: No relevance prediction needed (all relevant)
        if args.skip_relevance:
            logging.info(
                'Skipping relevance prediction as per argument. Assuming all studies are relevant.')
            relevant_df = pd.read_csv(csv_file)
        # Case 2: Relevance predictions already exist, load them (keep only relevant ones)
        elif rel_pred:
            logging.info(
                f'Relevance predictions for date {retrieval_date} already exist. Skipping prediction.')
            relevant_df = pd.read_csv(rel_pred)
            relevant_df = relevant_df[relevant_df['prediction'] == 1]
            logging.info(f'Loaded existing relevant studies from {rel_pred}')
        # Case 3: Need to run relevance prediction
        else:
            start = datetime.now(zurich)
            # Predict relevance first
            relevant_model = next(
                (m for m in model_info if m['task'].lower() == 'relevant'), None)
            model, tokenizer = load_model(
                relevant_model['model_path'], relevant_model['task'])
            logging.info(
                f'Loaded relevance model: {relevant_model["model_path"]}')
            
            # Drop samples with missing abstract or title and log the number of dropped samples
            relevant_df = pd.read_csv(csv_file)
            initial_count = len(relevant_df)
            # replace all nana with empty string
            relevant_df.fillna('', inplace=True)
            relevant_df = relevant_df[relevant_df['abstract'] != '']
            dropped_count = initial_count - len(relevant_df)
            if dropped_count > 0:
                logging.warning(
                    f'Dropped {dropped_count} samples due to missing abstract or title. Remaining samples: {len(relevant_df)}')
            
            data = SimpleDataset(relevant_df, tokenizer,
                                 multilabel=False, is_ner=False)
            relevant_predictions_df = predict(
                model, data, threshold=relevant_model['prediction_threshold'], batch_size=args.batch_size)
            logging.info('Completed predictions of relevance model.')

            # Drop the 'text' column from original_df to avoid suffixes after merge
            relevant_predictions_df = relevant_predictions_df.merge(relevant_df.drop(
                columns=['text']), left_on='id', right_on='pubmed_id', how='left')

            end = datetime.now(zurich)
            time_passed = end - start

            relevant_output_file = f'studies_{retrieval_date}_{format_timedelta_hms(time_passed)}.csv'
            os.makedirs(RELEVANT_STUDIES, exist_ok=True)
            relevant_predictions_df.to_csv(os.path.join(
                RELEVANT_STUDIES, relevant_output_file), index=False)
            nr_relevant = relevant_predictions_df['prediction'].sum()
            nr_irrelevant = len(relevant_predictions_df) - nr_relevant
            logging.info(
                f'Saved relevance predictions ({nr_relevant} relevant, {nr_irrelevant} irrelevant) to {os.path.join(RELEVANT_STUDIES, relevant_output_file)}')
            relevant_df = relevant_predictions_df[relevant_predictions_df['prediction'] == 1]

        # Now predict classification
        class_pred = check_if_pred_exist(
            FINAL_PRED, retrieval_date, str_contain='class')

        if class_pred:
            logging.info(
                f'Classification {retrieval_date} already exist. Skipping prediction.')

        else:
            logging.info(f'Running classification of {len(relevant_df)} relevant studies.')
            start = datetime.now(zurich)
            dfs = []
            for m in model_info:
                if m['task'].lower() == 'relevant' or m['task'] == 'NER':
                    continue  # already processed
                model, tokenizer = load_model(m['model_path'], m['task'])
                logging.info(
                    f'Loaded model: {m["model_path"]} for task: {m["task"]}')
                is_ner = 'ner' in m['task'].lower()
                data = SimpleDataset(relevant_df, tokenizer,
                                     multilabel=m['is_multilabel'], is_ner=is_ner)
                predictions_df = predict(
                    model, data, threshold=m['prediction_threshold'], batch_size=args.batch_size)
                logging.info(
                    f'Completed predictions for model: {m["model_path"]}')
                processed_data = []
                model_name = os.path.basename(os.path.dirname(m['model_path']))
                id2label = {int(k): v for k, v in m['id2label'].items()}

                for _, row in predictions_df.iterrows():
                    # TODO: Check if it is one-hot encoded
                    # multilabel: prediction: list[int] (one-hot encoded), probability: list[float]
                    # single label: prediction: int, probability: list[float]

                    if not data.is_multilabel:
                        predictions = list([row['prediction']])

                    else:
                        predictions = row['prediction']

                    for i, pred in enumerate(predictions):
                        pred_dict = {
                            'id': row['id'],
                            'task': m['task'],
                            'label': id2label[pred],
                            'probability': row['probability'][i],
                            'is_multilabel': m['is_multilabel'],
                            'model': model_name
                        }
                        processed_data.append(pred_dict)

                dfs.append(pd.DataFrame(processed_data))

            final_df = pd.concat(dfs, ignore_index=True)
            time_passed = datetime.now(zurich) - start
            pred_filename = f'class_predictions_{retrieval_date}_{format_timedelta_hms(time_passed)}.csv'
            final_df.to_csv(os.path.join(
                FINAL_PRED, pred_filename), index=False)
            logging.info(
                f'Saved class predictions to {os.path.join(FINAL_PRED, pred_filename)}')

        ner_pred = check_if_pred_exist(
            FINAL_PRED, retrieval_date, str_contain='ner')
        if ner_pred:
            logging.info(
                f'NER predictions for date {retrieval_date} already exist. Skipping prediction.')
        else:
            start = datetime.now(zurich)
            ner_model = next(
                (m for m in model_info if m['task'].lower() == 'ner'), None)
            model, tokenizer = load_model(
                ner_model['model_path'], ner_model['task'])
            id2label = {int(k): v for k, v in ner_model['id2label'].items()}
            logging.info(f'Loaded NER model: {ner_model["model_path"]}')
            data = SimpleDataset(relevant_df, tokenizer,
                                 multilabel=False, is_ner=True)
            ner_predictions_df = predict(model, data, batch_size=args.batch_size)
            logging.info('Completed predictions for NER model.')
            processed_data = []
            model_name = os.path.basename(
                os.path.dirname(ner_model['model_path']))
            id2label = {int(k): v for k, v in id2label.items()}

            for _, row in ner_predictions_df.iterrows():
                pred_dict = {
                    'id': row['id'],
                    'text': row['text'],
                    'tokens': row['tokens'],
                    'ner_tags': [id2label[i] for i in row['pred_labels']],
                    'probabilities': row['probabilities'],
                    'model': model_name
                }

                processed_data.append(pred_dict)
            end = datetime.now(zurich)
            time_passed = end - start
            ner_output_file = f'ner_predictions_{retrieval_date}_{format_timedelta_hms(time_passed)}.csv'
            pd.DataFrame(processed_data).to_csv(
                os.path.join(FINAL_PRED, ner_output_file), index=False)
            logging.info(
                f'Saved NER predictions to {os.path.join(FINAL_PRED, ner_output_file)}')

        logging.info('Prediction process completed successfully.')

    except Exception as e:
        logging.error(f'Error during prediction process: {e}', exc_info=True)


if __name__ == "__main__":
    main()
