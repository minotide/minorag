from minorag.indexer import index_code
from minorag.retriever import query_loop
from minorag.web import app


def main():
    print("1 - Indexar código")
    print("2 - Fazer perguntas (terminal)")
    print("3 - Abrir interface web")

    choice = input("> ")

    if choice == "1":
        index_code()
    elif choice == "3":
        print("Servidor web iniciado em http://localhost:5000")
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        query_loop()


if __name__ == "__main__":
    main()
