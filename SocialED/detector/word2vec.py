import argparse
import os
import pandas as pd
import numpy as np
from gensim.models import Word2Vec
from sklearn.model_selection import train_test_split
from sklearn import metrics
import logging
from sklearn.cluster import KMeans
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataset.dataloader import DatasetLoader
# Setup logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


class WORD2VEC:
    r"""The Word2Vec model for social event detection that uses word embeddings 
    to detect events in social media data.

    .. note::
        This detector uses word embeddings to identify semantic relationships
        and detect events in social media data. The model requires a dataset
        object with a load_data() method.

    See :cite:`mikolov2013efficient` for details.

    Parameters
    ----------
    dataset : object
        The dataset object containing social media data.
        Must provide load_data() method that returns the raw data.
    vector_size : int, optional
        Dimensionality of word vectors. Default: ``100``.
    window : int, optional
        Maximum distance between current and predicted word. Default: ``5``.
    min_count : int, optional
        Minimum word frequency. Default: ``1``.
    sg : int, optional
        Training algorithm: Skip-gram (1) or CBOW (0). Default: ``1``.
    file_path : str, optional
        Path to save model files. Default: ``'../model/model_saved/Word2vec/word2vec_model.model'``.
    """
    def __init__(self,
                 dataset,
                 vector_size=100, 
                 window=5,
                 min_count=1,
                 sg=1,
                 file_path='../model/model_saved/Word2vec/word2vec_model.model'):

        self.dataset = dataset.load_data()
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.sg = sg
        self.file_path = file_path
        self.df = None
        self.train_df = None
        self.test_df = None
        self.word2vec_model = None

    def preprocess(self):
        """
        Data preprocessing: tokenization, stop words removal, etc.
        """
        df = self.dataset[['filtered_words', 'event_id']].copy()
        df['processed_text'] = df['filtered_words'].apply(
            lambda x: [str(word).lower() for word in x] if isinstance(x, list) else [])
        self.df = df
        return df

    def fit(self):
        """
        Train the Word2Vec model and save it to a file.
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        train_df, test_df = train_test_split(self.df, test_size=0.2, random_state=42)
        self.train_df = train_df
        self.test_df = test_df

        sentences = train_df['processed_text'].tolist()

        logging.info("Training Word2Vec model...")
        word2vec_model = Word2Vec(sentences=sentences, vector_size=self.vector_size, window=self.window,
                                  min_count=self.min_count, sg=self.sg)
        logging.info("Word2Vec model trained successfully.")

        # Save the trained model to a file
        word2vec_model.save(self.file_path)
        logging.info(f"Word2Vec model saved to {self.file_path}")

        self.word2vec_model = word2vec_model
        return word2vec_model

    def load_model(self):
        """
        Load the Word2Vec model from a file.
        """
        logging.info(f"Loading Word2Vec model from {self.file_path}...")
        word2vec_model = Word2Vec.load(self.file_path)
        logging.info("Word2Vec model loaded successfully.")

        self.word2vec_model = word2vec_model
        return word2vec_model

    def document_vector(self, document):
        """
        Create a document vector by averaging the Word2Vec embeddings of its words.
        """
        words = [word for word in document if word in self.word2vec_model.wv]
        if words:
            return np.mean(self.word2vec_model.wv[words], axis=0)
        else:
            return np.zeros(self.vector_size)

    def detection(self):
        """
        Detect events by representing each document as the average Word2Vec embedding of its words.
        """
        self.load_model()  # Ensure the model is loaded before making detections

        test_vectors = self.test_df['processed_text'].apply(self.document_vector)
        predictions = np.stack(test_vectors)

        ground_truths = self.test_df['event_id'].tolist()
        kmeans = KMeans(n_clusters=len(set(ground_truths)), random_state=42)
        predictions = kmeans.fit_predict(predictions)

        return ground_truths, predictions

    def evaluate(self, ground_truths, predictions):
        """
        Evaluate the model.
        """

        # Calculate Adjusted Rand Index (ARI)
        ari = metrics.adjusted_rand_score(ground_truths, predictions)
        print(f"Adjusted Rand Index (ARI): {ari}")

        # Calculate Adjusted Mutual Information (AMI)
        ami = metrics.adjusted_mutual_info_score(ground_truths, predictions)
        print(f"Adjusted Mutual Information (AMI): {ami}")

        # Calculate Normalized Mutual Information (NMI)
        nmi = metrics.normalized_mutual_info_score(ground_truths, predictions)
        print(f"Normalized Mutual Information (NMI): {nmi}")

        return ari, ami, nmi

    def detection_by_day(self):
        """Run detection on daily slices of the dataset."""
        all_preds = []
        all_truths = []
        original_df = self.dataset.copy()
        df = self.dataset.copy()
        df['created_at'] = pd.to_datetime(df['created_at'])
        for day in sorted(df['created_at'].dt.date.unique()):
            self.dataset = df[df['created_at'].dt.date == day].reset_index(drop=True)
            self.preprocess()
            self.fit()
            gts, preds = self.detection()
            all_preds.extend(preds)
            all_truths.extend(gts)
        self.dataset = original_df
        return all_truths, all_preds


