import os
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException

from cover_letter_utility import Utility
from models import LoginUser, SignUpUser, CL, GoogleUser


app = FastAPI()
load_dotenv(".env")

origins = [
    "chrome-extension://njkagfnbfcchbifiohjgllfgabnikdgb"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/signup")
async def signup(user: SignUpUser):
    result = Utility.create_new_user(user.email, user.name, user.password)
    if isinstance(result, int):
        raise HTTPException(
            status_code=200, detail="Successfully created account")
    else:
        raise HTTPException(
            status_code=422, detail=result)


@app.post('/login')
async def login(user: LoginUser):
    result = Utility.login_user(user.email, user.password)
    if isinstance(result, int):
        return {"user_id": result}
    else:
        raise HTTPException(
            status_code=500, detail="Failed to log in. Please try again")


@app.post("/upload-cv")
async def save_doc(cv: UploadFile, user_id: int = Form(...)):
    type = Utility.check_type(cv.filename)
    if type not in ["pdf", "word"]:
        raise HTTPException(
            status_code=422, detail="Incorrect file type. Must be word or PDF")

    if type == "pdf":
        docs = Utility.read_pdf(cv.file)
    elif type == "word":
        docs = Utility.read_word(cv.file)

    if Utility.add_doc_to_table(docs, user_id):
        raise HTTPException(
            status_code=200, detail="CV Added Successfully")
    else:
        raise HTTPException(
            status_code=500, detail="Failed to add CV. Please try again")


@app.post("/cover-letter")
async def get_cover_letter(info: CL):
    rel_docs = Utility.get_related_docs(info.user_id, info.job_description)
    cover_letter = Utility.generate_cover_letter(rel_docs, info.job_description)
    if cover_letter:
        return {"cover_letter": cover_letter}
    else:
        raise HTTPException(
            status_code=415, detail="Failed to make cover letter. Please try again")


@app.post("/google-signup")
async def google_signup(email: str, name: str):
    result = Utility.get_user_id(email)
    if result:
        raise HTTPException(
            status_code=420, detail="User already exists. Please login")
    else:
        result = Utility.create_new_user(
            email, name=name, password=os.getenv("GOOGLE_PLACEHOLDER_PASSWORD"))
        if result:
            return {"user_id": result}
        else:
            raise HTTPException(
                status_code=500, detail="Error signing up user. Please try again")


@app.post("/google-login")
async def google_login(user: GoogleUser):
    result = Utility.login_user(user.email, oauth="google")
    if isinstance(result, int):
        return {"user_id": result}
    else:
        result = Utility.create_new_user(
            user.email, user.name, password=os.getenv("GOOGLE_PLACEHOLDER_PASSWORD"))
        if result:
            return {"user_id": result}
        else:
            raise HTTPException(
                status_code=500, detail="Error signing up user. Please try again")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", reload=True)
