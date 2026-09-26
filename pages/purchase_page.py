from textwrap import dedent

from nicegui import ui


@ui.page("/purchase")
def purchase_page() -> None:
    access_md = dedent("""
        ## Free Trainers

        All four WES350 conjugation trainers are free to use.

        **No payment, registration, or login is required.** Open any trainer
        from the home page and start practicing.

        Optional accounts, registration, login, and logout remain available.
        Administrative functions remain protected.
        """).strip()

    with ui.card().classes("w-full max-w-2xl mx-auto my-4"):
        ui.markdown(access_md)

    portfolio_md = dedent("""
        ## Portfolio Version

        This source-code version is preserved for professional portfolio and
        software-engineering demonstration purposes.

        The current portfolio version has no automated checkout or public
        payment workflow. The original manual access/payment workflow is
        historical and is no longer required to use the trainers.
        """).strip()

    with ui.card().classes("w-full max-w-2xl mx-auto my-4"):
        ui.markdown(portfolio_md)
