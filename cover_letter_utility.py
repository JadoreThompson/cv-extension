import os
from dotenv import load_dotenv

from transformers import BertModel, BertTokenizer
import torch

import docx
from pypdf import PdfReader

from db_connection import get_db_connection


load_dotenv(".env")


class Utility:
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
    EMBEDDING_MODEL = BertModel.from_pretrained(EMBEDDING_MODEL_NAME)
    TOKENIZER = BertTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)

    @staticmethod
    def check_type(filename):
        if filename[-4:] == "docx":
            return "word"
        elif filename[-3:] == "pdf":
            return "pdf"
        else:
            return "file type not valid, must be word (.docx) or pdf (.pdf) "

    @staticmethod
    def read_word(filename):
        doc = docx.Document(filename)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)

    @staticmethod
    def read_pdf(filename):
        reader = PdfReader(filename)
        pages = len(reader.pages)
        print(f"Amount of Pages: {pages}")

        full_text = []
        for i in range(0, pages):
            page = reader.pages[i]
            full_text.append(page.extract_text())
        return full_text

    @staticmethod
    def generate_embeddings(text):
        encoding = Utility.TOKENIZER.encode_plus(
            text,
            padding=True,
            truncation=True,
            return_tensors="pt",
            add_special_tokens=True,
            max_length=768
        )
        with torch.no_grad():
            outputs = Utility.EMBEDDING_MODEL(
                encoding["input_ids"],
                attention_mask=encoding["attention_mask"]
            )
            word_embeddings = outputs.last_hidden_state[:, 0, ].numpy().flatten()
            return word_embeddings

    @staticmethod
    def get_user_id(email):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.excute("SELECT id FROM users WHERE email=%s", (email, ))

    @staticmethod
    def add_doc_to_table(text):
        text_embeds = Utility.generate_embeddings(text)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.excute("""
                    INSERT INTO users (cv, embedding)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING; 
                """, (text, text_embeds, ))
