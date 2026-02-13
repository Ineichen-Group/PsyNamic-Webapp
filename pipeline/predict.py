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
from datetime import timedelta, datetime
from data.populate import check_if_pred_exist
import argparse

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

            tokens = self.tokenizer.convert_ids_to_tokens(encoding["input_ids"])
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


def predict(model: Union[AutoModelForTokenClassification, AutoModelForSequenceClassification], test_dataset: SimpleDataset, threshold: float = 0.5) -> pd.DataFrame:
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

        # Run inference per chunk
        for i in range(len(test_dataset)):
            sample = test_dataset[i]

            input_ids = torch.tensor(
                [test_dataset.tokenizer.convert_tokens_to_ids(sample["tokens"])],
                device=device
            )

            attention_mask = torch.ones_like(input_ids, device=device)

            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits.squeeze(0)  # (seq_len, num_labels)
                probs = torch.softmax(logits, dim=-1)

            all_logits.append(logits.cpu().numpy())
            all_probs.append(probs.cpu().numpy())

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
                            word = test_dataset.tokenizer.convert_tokens_to_string(current_word_tokens)
                            merged_tokens.append(word)
                            merged_labels.append(current_word_label)
                            merged_probs.append(current_word_prob)

                        # Start new word
                        current_word_tokens = [token]
                        current_word_label = int(preds_chunk[j])   # first subtoken label
                        current_word_prob = float(probs_chunk[j].max())
                        current_word_id = word_id

                    else:
                        current_word_tokens.append(token)

                # Save last word
                if current_word_tokens:
                    word = test_dataset.tokenizer.convert_tokens_to_string(current_word_tokens)
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

        for i in range(len(test_dataset)):
            sample = test_dataset[i]

            encoding = test_dataset.tokenizer(
                sample["text"],
                return_tensors="pt",
                truncation=True,
                max_length=test_dataset.max_len,
                padding="max_length"
            )

            input_ids = encoding["input_ids"].to(device)
            attention_mask = encoding["attention_mask"].to(device)

            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits.squeeze(0)

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
    """Get lastest csv from data directory, taken the date in filename, e.g. pubmed_results_20250813_00:00:08"""
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError(
            "No CSV files found in the specified directory.")

    # Extract date from filenames and find the latest
    latest_file = max(csv_files, key=lambda x: datetime.strptime(
        x.split('_')[2], "%Y%m%d"))
    return os.path.join(data_dir, latest_file)


def extract_retrieval_date_from_filename(filename: str) -> str:
    """pubmed_results_20231216_20260112_00:00:10.csv -> 20260112"""
    base_name = os.path.basename(filename)
    parts = base_name.split('_')
    try: 
        return parts[-2]
    except:
        return "unknown_date"


def format_timedelta_hms(td: timedelta) -> str:
    """Format timedelta to HH-MM-SS string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}-{minutes:02d}-{seconds:02d}"


def cleanup_old_logs(log_dir: str, keep_n: int = 50):
    """Deletes old log files, keeping only the N most recent ones."""
    try:
        log_files = [f for f in os.listdir(log_dir) if f.startswith('predict_') and f.endswith('.log')]
        if len(log_files) <= keep_n:
            return

        # Sort files by creation time (embedded in filename)
        log_files.sort(key=lambda x: datetime.strptime(x.split('_')[1], "%Y%m%d"), reverse=True)

        # Files to delete
        files_to_delete = log_files[keep_n:]

        for f in files_to_delete:
            os.remove(os.path.join(log_dir, f))
            logging.info(f"Removed old log file: {f}")

    except Exception as e:
        logging.warning(f"Could not clean up old logs: {e}")


def main():

    # add argument parser, if input file is given, use that instead of latest file
    # -i or --input_file
    # add output directory argument
    # -o or --output_dir

    parser = argparse.ArgumentParser(description="Run prediction pipeline")
    parser.add_argument(
        '-i', '--input_file',
        type=str,
        help='Path to the input CSV file for prediction. If not provided, the latest file from the data directory will be used.'
    )
    parser.add_argument(
        '--skip_relevance',
        action='store_true',
        help='Skip relevance prediction step.'
    )
    args = parser.parse_args()

    # Setup logging
    log_dir = os.path.join(SCRIPT_DIR, 'log')
    os.makedirs(log_dir, exist_ok=True)

    # Clean up old logs before creating a new one
    cleanup_old_logs(log_dir)

    log_filename = f'predict_{datetime.now(zurich).strftime("%Y%m%d_%H%M%S")}.log'
    log_path = os.path.join(log_dir, log_filename)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )
    logging.info('Prediction process started.')
    PUBMED_DATA_DIR = 'data/pubmed_fetch_results'
    MODEL_INFO = 'pipeline/model_paths.json'
    FINAL_PRED = 'data/predictions'
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
        logging.info(f'Loaded model info from {MODEL_INFO}')     

        rel_pred = check_if_pred_exist(RELEVANT_STUDIES, retrieval_date)
        # Check if relevance predictions already exist
        if rel_pred:
            logging.info(f'Relevance predictions for date {retrieval_date} already exist. Skipping prediction.')
            relevant_df = pd.read_csv(rel_pred)
            logging.info(f'Loaded existing relevant studies from {rel_pred}')
        elif args.skip_relevance:
            logging.info('Skipping relevance prediction as per argument. Assuming all studies are relevant.')
            relevant_df = pd.read_csv(csv_file)
        else:
            start = datetime.now(zurich)
            # Predict relevance first
            relevant_model = next(
                (m for m in model_info if m['task'].lower() == 'relevant'), None)
            model, tokenizer = load_model(relevant_model['model_path'], relevant_model['task'])
            logging.info(f'Loaded relevant model: {relevant_model["model_path"]}')
            data = SimpleDataset(csv_file, tokenizer,
                                multilabel=False, is_ner=False)
            relevant_predictions_df = predict(
                model, data, threshold=relevant_model['prediction_threshold'])
            logging.info('Completed predictions for relevance model.')
            relevant_label_id = next(
                (k for k, v in relevant_model['id2label'].items() if v == 'relevant'), None)
            relevant_df = relevant_predictions_df[relevant_predictions_df['prediction'] == int(
                relevant_label_id)]
            # Add all others columns from original csv
            original_df = pd.read_csv(csv_file)
            # Drop the 'text' column from original_df to avoid suffixes after merge
            relevant_df = relevant_df.merge(original_df.drop(columns=['text']), left_on='id', right_on='pubmed_id', how='left')
            
            end = datetime.now(zurich)
            time_passed = end - start

            relevant_output_file = f'studies_{retrieval_date}_{format_timedelta_hms(time_passed)}.csv'
            os.makedirs(RELEVANT_STUDIES, exist_ok=True)
            relevant_df.to_csv(os.path.join(RELEVANT_STUDIES, relevant_output_file), index=False)
            logging.info(f'Saved relevant studies prediction to {os.path.join(RELEVANT_STUDIES, relevant_output_file)}')

        # Now predict classification
        class_pred = check_if_pred_exist(FINAL_PRED, retrieval_date, str_contain='class')
        
        if class_pred:
            logging.info(f'Classification {retrieval_date} already exist. Skipping prediction.')
        
        else:
            start = datetime.now(zurich)
            dfs = []
            for m in model_info:
                if m['task'].lower() == 'relevant' or m['task'] == 'NER':
                    continue  # already processed
                model, tokenizer = load_model(m['model_path'], m['task'])
                logging.info(f'Loaded model: {m["model_path"]} for task: {m["task"]}')
                is_ner = 'ner' in m['task'].lower()
                data = SimpleDataset(relevant_df, tokenizer,
                                    multilabel=m['is_multilabel'], is_ner=is_ner)
                predictions_df = predict(
                    model, data, threshold=m['prediction_threshold'])
                logging.info(f'Completed predictions for model: {m["model_path"]}')
                processed_data = []
                model_name = os.path.basename(os.path.dirname(m['model_path']))
                id2label = {int(k): v for k, v in m['id2label'].items()}

                for _, row in predictions_df.iterrows():
                    #TODO: Check if it is one-hot encoded
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
            final_df.to_csv(os.path.join(FINAL_PRED, pred_filename), index=False)
            logging.info(f'Saved class predictions to {os.path.join(FINAL_PRED, pred_filename)}')

        ner_pred = check_if_pred_exist(FINAL_PRED, retrieval_date, str_contain='ner')
        if ner_pred:
            logging.info(f'NER predictions for date {retrieval_date} already exist. Skipping prediction.')
        else:
            start = datetime.now(zurich)
            ner_model = next(
                (m for m in model_info if m['task'].lower() == 'ner'), None)
            model, tokenizer = load_model(ner_model['model_path'], ner_model['task'])
            id2label = {int(k): v for k, v in ner_model['id2label'].items()}
            logging.info(f'Loaded NER model: {ner_model["model_path"]}')
            data = SimpleDataset(relevant_df, tokenizer,
                                multilabel=False, is_ner=True)
            ner_predictions_df = predict(model, data)
            logging.info('Completed predictions for NER model.')
            processed_data = []
            model_name = os.path.basename(os.path.dirname(ner_model['model_path']))
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
            pd.DataFrame(processed_data).to_csv(os.path.join(FINAL_PRED, ner_output_file), index=False)
            logging.info(f'Saved NER predictions to {os.path.join(FINAL_PRED, ner_output_file)}')

        logging.info('Prediction process completed successfully.')

    except Exception as e:
        logging.error(f'Error during prediction process: {e}', exc_info=True)


if __name__ == "__main__":
    main()
