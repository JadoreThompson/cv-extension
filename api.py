import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# from cover_letter_utility import Utility


app = FastAPI()

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


@app.post("/upload-cv")
async def save_doc(cv: UploadFile):
    print({"file": cv})

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", reload=True)