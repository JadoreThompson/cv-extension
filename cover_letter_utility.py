import os
from dotenv import load_dotenv

import pandas as pd
from transformers import BertModel, BertTokenizer
import torch

import docx
from pypdf import PdfReader

from pgvector.psycopg2 import register_vector
from db_connection import get_db_connection, return_conn


load_dotenv(".env")


class Utility:
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
    EMBEDDING_MODEL = BertModel.from_pretrained(EMBEDDING_MODEL_NAME)
    TOKENIZER = BertTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)

    # Returns string of file type
    @staticmethod
    def check_type(filename):
        if filename[-4:] == "docx":
            return "word"
        elif filename[-3:] == "pdf":
            return "pdf"
        else:
            return "file type not valid, must be word (.docx) or pdf (.pdf) "

    # Returns String of word file content
    @staticmethod
    def read_word(filename):
        doc = docx.Document(filename)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text).encode("utf-8")

    # Returns String of pdf file content
    @staticmethod
    def read_pdf(filename):
        reader = PdfReader(filename)
        pages = len(reader.pages)
        print(f"Amount of Pages: {pages}")

        full_text = []
        for i in range(0, pages):
            page = reader.pages[i]
            full_text.append(page.extract_text().encode("utf-8"))
        return full_text

    # Returns the embeddings as a numpy 768 dimensional array
    @staticmethod
    def generate_embeddings(text):
        encoding = Utility.TOKENIZER.encode_plus(
            str(text[0]),
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

    # Creates new user in users table
    @staticmethod
    def create_new_user(email, password=None):
        user_dict = {"email": email, "password": password}
        df = pd.DataFrame(user_dict)
        cols = ", ".join(df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        values = (email, password)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        INSERT INTO users ({cols})
                        VALUES ({placeholders});
                    """, values)
                    conn.commit()
        except Exception as e:
            conn.rollback()
            print(e)
        finally:
            return_conn(conn)

    # Returns the user ID as int
    @staticmethod
    def get_user_id(email):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM users
                        WHERE email = %s;
                    """, (email, ))

                    result = cur.fetchone()
                    if result:
                        user_id = result[0]
                        return user_id
                    else:
                        return None
        except Exception as e:
            print(e)
        finally:
            return_conn(conn)

    '''
        Performs SQL query inserting,
        both the text representation of document and it's embeds
    '''
    @staticmethod
    def add_doc_to_table(text, user_id):
        text_embeds = Utility.generate_embeddings(text)

        with get_db_connection() as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        UPDATE users
                        SET cv = %s, embedding = %s
                        WHERE id = %s; 
                    """, (text, text_embeds, user_id, ))
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print("\n", e)
                finally:
                    return_conn(conn)
