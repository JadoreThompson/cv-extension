from cover_letter_utility import Utility


filename = "J.pdf"
filename_type = Utility.check_type(filename)
print("File Type: ", filename_type)


if filename_type == "word":
    doc = Utility.read_word(filename)
    doc_embeds = Utility.generate_embeddings(doc)
elif filename_type == "pdf":
    doc = Utility.read_pdf(filename)
    doc_embeds = Utility.generate_embeddings(doc)
else:
    print(filename_type)

# Simulating the user pasting job desc
with open("desc.txt", "r") as f:
    jobdesc = f.read()

jobdesc_embeds = Utility.generate_embeddings(jobdesc)
