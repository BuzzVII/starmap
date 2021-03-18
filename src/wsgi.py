from starlink import create_app

app = create_app()

if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.run()
