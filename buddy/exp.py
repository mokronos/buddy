import marimo

__generated_with = "0.11.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    print(list(sys.modules.keys()))

    return (sys,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
