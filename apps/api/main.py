from fastapi import FastAPI

app: FastAPI = FastAPI()


@app.get("/")
def main():
    return {"message": "Hello, it's me!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app")
