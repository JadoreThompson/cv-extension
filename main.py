from cover_letter_utility import Utility
from db_connection import get_db_connection, return_conn


def func0():
    filename = "J.pdf"
    filename_type = Utility.check_type(filename)
    print("File Type: ", filename_type)

    if filename_type == "word":
        doc = Utility.read_word(filename)
        user_id = Utility.get_user_id("testuser@gmail.com")
        print(f"User ID: {user_id}")
        Utility.add_doc_to_table(doc, user_id)
    elif filename_type == "pdf":
        doc = Utility.read_pdf(filename)
        user_id = Utility.get_user_id("testuser@gmail.com")
        Utility.add_doc_to_table(doc, user_id)
    else:
        print(filename_type)


def get_cover_letter():
    with open("desc.txt", "r") as f:
        job_desc = f.read()

    related_docs = Utility.get_related_docs(1, job_desc)
    print(Utility.generate_cover_letter(related_docs, job_desc))
    # return related_docs


if __name__ == "__main__":
    get_cover_letter()

