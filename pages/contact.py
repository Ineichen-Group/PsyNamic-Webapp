from dash import html
import dash_bootstrap_components as dbc


def contact_layout():
    return dbc.Container(
            [

                # Page title
                html.H1("Contact Us", className="my-4"),

                # Project description
                html.P(
                    [
                        "PsyNamic is a project from the STRIDE Lab (Medical Data Science Group) "
                        "at the Department of Clinical Research, University of Bern, which was formerly affiliated with the Center for Reproducible Science "
                        "at the University of Zurich. Learn more about our research at the ",
                        html.A(
                            "STRIDE Lab website",
                            href="https://ineichen-group.github.io/website/",
                            target="_blank",
                            className="text-primary",
                        ),
                        ".",
                    ],
                    className="mb-4",
                ),

                html.P(
                    [
                        "Is something not working as expected? Please report bugs by opening up an issue on ",
                        html.A(
                            "GitHub",
                            href="https://github.com/Ineichen-Group/PsyNamic-Webapp/issues",
                            target="_blank",
                            className="text-primary",
                        ),
                        ".",
                    ],
                    className="mb-5",
                ),

                # Team section
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Principal Investigator", className="mb-3"),
                                html.P("Benjamin Ineichen"),
                                html.P(
                                    [
                                        "Email: ",
                                        html.A(
                                            "benjamin.ineichen@unibe.ch",
                                            href="mailto:benjamin.ineichen@unibe.ch",
                                            className="text-primary",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.P(
                                    html.A(
                                        "More about Benjamin Ineichen",
                                        href="https://ineichen-group.github.io/website/people/ineichen-benjamin-victor/index.html",
                                        target="_blank",
                                        className="text-secondary",
                                    )
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.H4("Developer", className="mb-3"),
                                html.P("Vera Bernhard"),
                                html.P(
                                    [
                                        "Email: ",
                                        html.A(
                                            "vera.bernhard@unibe.ch",
                                            href="mailto:vera.bernhard@unibe.ch",
                                            className="text-primary",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.P(
                                    html.A(
                                        "More about Vera Bernhard",
                                        href="https://ineichen-group.github.io/website/people/bernhard-vera/index.html",
                                        target="_blank",
                                        className="text-secondary",
                                    )
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-5",
                ),
                html.H3("Further Contributors", className="mb-3"),
                # Data annotators
                html.H4("Data Annotators", className="mt-3"),
                html.Ul(
                    [
                        html.Li("David Brüschweiler"),
                        html.Li("Julia Bugajska"),
                        html.Li("Bernard Hild"),
                        html.Li("Johann Liesner"),
                        html.Li("Pia Härvelid"),      
                    ],
                    className="small mb-4",
                ),

                # Clinical collaborators
                html.H4("Clinical Collaborators", className="mt-3"),
                html.Ul(
                    [
                        html.Li("Helena Aicher"),
                        html.Li("Milan Scheidegger"),
                    ],
                    className="small mb-5",
                ),

                # Affiliations
                html.H3("Affiliations", className="mb-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            html.A(
                                html.Img(
                                    src="/assets/unibe.png",
                                    alt="University of Bern",
                                    height="120",
                                ),
                                href="https://www.unibe.ch",
                                target="_blank",
                            ),
                            width=3,
                            className="text-center",
                        ),
                        dbc.Col(
                            html.A(
                                html.Img(
                                    src="/assets/dcr.png",
                                    alt="Department of Clinical Research",
                                    height="120",
                                ),
                                href="https://dcr.unibe.ch/",
                                target="_blank",
                            ),
                            width=3,
                            className="text-center",
                        ),
                        dbc.Col(
                            html.A(
                                html.Img(
                                    src="/assets/uzh.png",
                                    alt="University of Zurich",
                                    height="120",
                                ),
                                href="https://www.uzh.ch",
                                target="_blank",
                            ),
                            width=3,
                            className="text-center",
                        ),
                        dbc.Col(
                            html.A(
                                html.Img(
                                    src="/assets/crs.png",
                                    alt="Center for Reproducible Science",
                                    height="120",
                                ),
                                href="https://www.crs.uzh.ch/en.html",
                                target="_blank",
                            ),
                            width=3,
                            className="text-center",
                        ),
                    ],
                    className="my-4 align-items-center",
                ),
            ],
            fluid=True,
        )