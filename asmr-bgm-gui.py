from classes.app import App


def main():
    # Create the entire GUI program
    app = App()

    # Start the GUI event loop
    app.window.mainloop()

if __name__ == "__main__":
    main()