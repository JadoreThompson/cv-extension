import os
from dotenv import load_dotenv

import torch
from transformers import BertModel, BertTokenizer

import docx
from pypdf import PdfReader

from argon2 import PasswordHasher
from psycopg2 import IntegrityError
from db_connection import get_db_connection, return_conn

import google.generativeai as genai


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
        return "\n".join(full_text)

    # Returns String of pdf file content
    @staticmethod
    def read_pdf(filename):
        reader = PdfReader(filename)
        pages = len(reader.pages)

        full_text = []
        for i in range(0, pages):
            page = reader.pages[i]
            full_text.append(page.extract_text())
        return "\n".join(full_text)

    # Returns the embeddings as a numpy 768 dimensional array
    @staticmethod
    def generate_embeddings(text):
        # TODO: If necessary, implement text splitting
        encoding = Utility.TOKENIZER.encode_plus(
            text,
            padding=True,
            truncation=True,
            return_tensors="pt",
            add_special_tokens=True,
            max_length=512
        )
        with torch.no_grad():
            outputs = Utility.EMBEDDING_MODEL(
                encoding["input_ids"],
                attention_mask=encoding["attention_mask"],
            )
            word_embeddings = outputs.last_hidden_state[:, 0, ].numpy().flatten()
            return word_embeddings.tolist()

    # Creates new user in users table
    @staticmethod
    def create_new_user(email, password=None):
        if password:
            ph = PasswordHasher()
            hashed_pw = ph.hash(password)
            user_dict = {"email": email, "password": hashed_pw}
            values = (email, password)
        else:
            user_dict = {"email": email}
            values = (email,)

        cols = ", ".join(user_dict.keys())
        placeholders = ", ".join(["%s"] * len(user_dict.keys()))

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        INSERT INTO users ({cols})
                        VALUES ({placeholders})
                        RETURNING id;
                    """, values)
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    return user_id
        except IntegrityError as e:
            conn.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                print("Duplicate entry: A user with this email already exists.")
            else:
                print(f"Database error: {e}")
                return None
        except Exception as e:
            conn.rollback()
            print(f"Unexpected error: {e}")
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
            conn.rollback()
            print(f"Unexpected error: {e}")
            return None
        finally:
            return_conn(conn)

    '''
        Performs SQL query inserting,
        both the text representation of document and it's embeds
    '''

    @staticmethod
    def remove_special_characters(s):
        allowed_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._")
        filtered_chars = [c if c in allowed_chars else " " for c in s]
        return ''.join(filtered_chars)

    @staticmethod
    def add_doc_to_table(text, user_id):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    lines = text.split("\n")
                    for line in lines:
                        if line.strip():
                            line = Utility.remove_special_characters(line)
                            line_embed = Utility.generate_embeddings(line)
                            cur.execute("""
                                INSERT INTO cv_lines (user_id, line, embedding)
                                VALUES (%s, %s, %s);
                            """, (user_id, line, line_embed))
                    conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error adding document to table: {e}")
        finally:
            return_conn(conn)

    @staticmethod
    def get_related_docs(user_id, desc, limit=10):
        desc = Utility.remove_special_characters(desc)
        desc_embeds = Utility.generate_embeddings(desc)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT line
                        FROM cv_lines
                        WHERE user_id = %s
                        ORDER BY embedding <=> %s::vector ASC
                        LIMIT %s;
                    """, (user_id, desc_embeds, limit))
                    rows = cur.fetchall()
                    return rows
        except Exception as e:
            conn.rollback()
            print(e)
            return None
        finally:
            return_conn(conn)

    @ staticmethod
    # def generate_cover_letter():
    def generate_cover_letter(related_docs, job_desc, bio=None):
        try:
            genai.configure(api_key=os.getenv("GEMINI_APIKEY"))
            TEXT_GEN_MODEL = genai.GenerativeModel("gemini-1.5-pro")

            full_prompt = f"""
            Job description: {job_desc}
            
            Question: Generate a cover letter for the job description tailored to the company.
            """

            full_prompt += "Context:\n"
            for doc in related_docs:
                full_prompt += f"""
                {doc[0]}\n
                """

            full_prompt += """
            The structure should be:
            
            - Opening Paragraph: Introduce myself, mention my most relevant pieces of experience,
            highlight my most relevant pieces of experience. Establish my passion for the job, mentioning
            my relevant experience and how it fits my expertise.Generate a short tale of why the company
            fits me by researching the company on the internet and producing a short summary for the company
            that you can use a database to cross reference. Conclude this paragraph leading onto the next 
            paragraph.
            
            - Middle Paragraph: Talk about specifics, pin point the most important requirements for the role
            and pair my context with it. Going deeper into my experience means explaining the steps I took
            and impact I made through my experience. This paragraph is all about making myself seem like
            the best fit for this role.
            
            - Closing Paragraph: Thank the employer for their time and consideration. If there are any
            requirements for the role not addressed in the context. Address them in this paragraph. Be sure
            to not make myself feel unqualified, instead when addressing my gaps make me sound like the
            best because of these gaps. Express interest in the role and lead onto the next stage in the
            recruitment process.
            
            - Close and Signature: Choose between (Sincerely, Regards, Best, Respectfully, Thank You,
            Thank You for Your Consideration)
            
            Make sure there are no bold characters in the response. The response mustn't require the user
            to add more information to it. You must write it to completion. The whole cover letter should be
            no larger than 500 words
            
            """

            if bio:
                full_prompt += bio

            full_prompt += "Answer: "

            completion = TEXT_GEN_MODEL.generate_content(full_prompt)
            completion = completion.candidates[0].content.parts[0].text
            completion = completion.replace(["*", "**"], "")

            return completion
        except Exception as e:
            print(e)
            return None

