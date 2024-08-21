from cover_letter_utility import Utility


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
    print(f"User ID: {user_id}")
    print(f"User ID Type: {type(user_id)}")
    Utility.add_doc_to_table(doc, user_id)

else:
    print(filename_type)


# Simulating the user pasting job desc
with open("desc.txt", "r") as f:
    jobdesc = f.read()

jobdesc_embeds = Utility.generate_embeddings(jobdesc)
