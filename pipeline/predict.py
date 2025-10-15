
import os
import logging
import numpy as np
from ast import literal_eval
import pandas as pd
import torch
import json
import torch.nn.functional as F
from torch.utils.data import Dataset

# Assuming Trainer, DataSplit, DataSplitBIO are defined elsewhere in your project
from typing import Union
from transformers import Trainer, AutoModelForTokenClassification, AutoModelForSequenceClassification, AutoTokenizer

from datetime import datetime
import pytz
import pandas as pd
from torch.utils.data import Dataset

zurich = pytz.timezone('Europe/Zurich')


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

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        id_ = row[self.ID_COL]
        text = row[self.TEXT_COL]

        if self.is_ner:
            # Tokenize for NER, return dummy labels
            tokens = self.tokenizer.tokenize(text)
            dummy_label = [-100] * len(tokens)  # ignored by loss function
            return {
                'id': id_,
                'tokens': tokens,
                'labels': dummy_label
            }
        else:
            # Standard tokenization for classification/regression
            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=self.max_len,
                return_tensors='pt'
            )
            return {
                'id': id_,
                **{key: val.squeeze(0) for key, val in encoding.items()}
            }


def predict(trainer: Trainer, test_dataset: SimpleDataset, threshold: float = 0.5) -> pd.DataFrame:
    """
    Predicts the labels for the test dataset and saves predictions to a CSV.
    Works for classification and token-level NER using a SimpleDataset.
    """

    # Make predictions
    predictions = trainer.predict(test_dataset)
    pred_data = []

    # Check if this is NER
    if test_dataset.is_ner:
        # predictions.predictions shape: (num_samples, seq_len, num_labels)
        logits = torch.tensor(predictions.predictions)
        probs = F.softmax(logits, dim=-1)
        pred_labels_idx = torch.argmax(
            probs, dim=-1).numpy()  # (num_samples, seq_len)

        for i, data in enumerate(test_dataset):
            id_ = data['id']
            tokens = data['tokens']
            dummy_labels = data['labels']  # all -100
            preds = pred_labels_idx[i]

            if len(preds) != len(tokens):
                # Sometimes tokenizers add special tokens, truncate predictions accordingly
                preds = preds[:len(tokens)]

            for token, pred_idx in zip(tokens, preds):
                pred_data.append({
                    "id": id_,
                    "token": token,
                    "prediction": test_dataset.labels[pred_idx],
                    "probability": probs[i, :len(tokens), pred_idx].tolist()
                })

    else:
        # Classification
        logits = torch.tensor(predictions.predictions)
        if getattr(test_dataset, 'is_multilabel', False):
            probs = torch.sigmoid(logits).numpy()
            pred_labels = (probs >= threshold).astype(int)
        else:
            probs = F.softmax(logits, dim=1).numpy(
            ) if logits.ndim > 1 else F.softmax(logits, dim=0).numpy()
            pred_labels = np.argmax(
                probs, axis=1) if logits.ndim > 1 else np.argmax(probs)

        for i, data in enumerate(test_dataset):
            id_ = data['id']
            text = data['text']
            pred_label = pred_labels[i] if logits.ndim > 1 else int(
                pred_labels)
            prob = probs[i].tolist() if logits.ndim > 1 else probs.tolist()

            pred_data.append({
                "id": id_,
                "text": text,
                "prediction": pred_label,
                "probability": prob
            })

    # Save to CSV
    df = pd.DataFrame(pred_data)
    return df


def load_model(model_path: str, task: str):
    # detect device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if 'ner' in task.lower():
        model = AutoModelForTokenClassification.from_pretrained(
            model_path).to(device)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path).to(device)

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    trainer = Trainer(model=model, tokenizer=tokenizer)
    return trainer


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


def check_if_pred_exist(pred_dir: str, retrieval_date: str) -> str:
    """Check if prediction file for the given retrieval date already exists."""
    pred_files = [f for f in os.listdir(pred_dir) if f.endswith('.csv')]
    for f in pred_files:
        if retrieval_date in f:
            return os.path.join(pred_dir, f)
    return ""

def main():
    # Setup logging
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, 'log')
    os.makedirs(log_dir, exist_ok=True)
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
        csv_file = get_latest_data(PUBMED_DATA_DIR)
        logging.info(f'Loaded latest data file: {csv_file}')
        now = datetime.now(zurich)
        date = now.strftime("%Y-%m-%d")
        dfs = []
        with open(MODEL_INFO, 'r', encoding='utf-8') as file:
            model_info = json.load(file)
        logging.info(f'Loaded model info from {MODEL_INFO}')

        # Check if predictions for this retrieval date already exist
        rel_pred = check_if_pred_exist(RELEVANT_STUDIES, date)
        if rel_pred:
            logging.info(f'Relevance predictions for date {date} already exist. Skipping prediction.')
            # load existing relevant predictions
            relevant_df = pd.read_csv(rel_pred)
            logging.info(f'Loaded existing relevant studies from {rel_pred}')
        
        else:
            # Predict relevance first
            relevant_model = next(
                (m for m in model_info if m['task'].lower() == 'relevant'), None)
            trainer = load_model(relevant_model['model_path'], relevant_model['task'])
            logging.info(f'Loaded relevant model: {relevant_model["model_path"]}')
            data = SimpleDataset(csv_file, trainer.tokenizer,
                                multilabel=False, is_ner=False)
            relevant_predictions_df = predict(
                trainer, data, threshold=relevant_model['prediction_threshold'])
            logging.info('Completed predictions for relevance model.')
            relevant_label_id = next(
                (k for k, v in relevant_model['id2label'].items() if v == 'relevant'), None)
            relevant_df = relevant_predictions_df[relevant_predictions_df['prediction'] == int(
                relevant_label_id)]
        
            # Write relevant studies to a CSV, extract retrieval time from filename
            retrieval_time = os.path.basename(csv_file).split('_')[2]  # yyyymmdd
            relevant_output_file = f'studies_{date}_{retrieval_time}.csv'
            os.makedirs(RELEVANT_STUDIES, exist_ok=True)
            relevant_df.to_csv(os.path.join(RELEVANT_STUDIES, relevant_output_file), index=False)
            logging.info(f'Saved relevant studies to {os.path.join(RELEVANT_STUDIES, relevant_output_file)}')

        clas_ner_pred = check_if_pred_exist(FINAL_PRED, date)
        if clas_ner_pred:
            logging.info(f'Classification/NER predictions for date {date} already exist. Skipping prediction.')
            return
        
        else: 
            for m in model_info:
                if m['task'].lower() == 'relevant':
                    continue  # already processed
                trainer = load_model(m['model_path'], m['task'])
                logging.info(f'Loaded model: {m["model_path"]} for task: {m["task"]}')
                data = SimpleDataset(relevant_df, trainer.tokenizer,
                                    multilabel=m['is_multilabel'], is_ner=('ner' in m['task'].lower()))
                predictions_df = predict(
                    trainer, data, threshold=m['prediction_threshold'])
                logging.info(f'Completed predictions for model: {m["model_path"]}')
                processed_data = []
                for _, row in predictions_df.iterrows():
                    for i, prob in enumerate(literal_eval(row['probability'])):
                        model_name = os.path.basename(os.path.dirname(m['model_path']))
                        pred_dict = {
                            'id': row['id'],
                            'task': m['task'],
                            'label': m['id2label'][i],
                            'probability': prob,
                            'is_multilabel': m['is_multilabel'],
                            'model': model_name
                        }
                        processed_data.append(pred_dict)
                dfs.append(pd.DataFrame(processed_data))

            final_df = pd.concat(dfs, ignore_index=True)
            time_passed = datetime.now(zurich) - now
            pred_filename = f'predictions_{date}_{time_passed}.csv'
            final_df.to_csv(os.path.join(FINAL_PRED, pred_filename), index=False)
            logging.info(f'Saved final predictions to {os.path.join(FINAL_PRED, pred_filename)}')
            logging.info('Prediction process completed successfully.')

    except Exception as e:
        logging.error(f'Error during prediction process: {e}', exc_info=True)


if __name__ == "__main__":
    main()
