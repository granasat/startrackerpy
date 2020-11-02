from server import app


def main():
    app.run(debug=True, host='0.0.0.0', port=4000, use_reloader=True)


if __name__ == "__main__":
    main()
