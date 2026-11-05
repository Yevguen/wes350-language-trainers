from textwrap import dedent

from nicegui import ui

CONTACT_EMAIL = "yevguenyi@gmail.com"
LAST_UPDATED_EN = "5 November 2026"
LAST_UPDATED_ES = "5 de noviembre de 2026"

PRIVACY_EN = dedent(f"""
    ## Privacy notice

    Last updated: {LAST_UPDATED_EN}

    **Who runs this site.** WES350, Multilingual Verb Conjugation Trainers, is a
    free, non-commercial portfolio project run by Yevhen Babko (GitHub: Yevguen),
    Málaga, Spain. Contact: {CONTACT_EMAIL}.

    **What data is processed.**

    - To deliver the pages, the hosting provider, Render, processes your IP
      address and technical details of your request, such as the page requested.
      The site itself keeps no logs of visitors' requests.
    - Answers you type in the trainers are sent to the server only to check them
      and show corrections. They are not stored.
    - The site has no visitor accounts: public registration is closed. The only
      accounts are the site administrator's own.
    - No analytics, advertising or tracking tools are used, and no data is sold
      or shared for marketing.
    - The site does not make automated decisions, including profiling, that
      produce legal or similarly significant effects.

    Providing your IP address is not a legal or contractual requirement, but it
    is technically necessary to deliver the site; without it, the site cannot be
    shown.

    **Why, and on what legal basis.** The legal basis for delivering the site,
    checking answers and using the necessary technical identifiers is my
    legitimate interest in providing a working, secure service and fixing
    problems (Article 6(1)(f) GDPR).

    **Who else processes it.** Render Services, Inc. (San Francisco, USA) hosts
    the site under its data processing addendum. Render may also process certain
    service usage data as an independent controller under its privacy policy.
    The data may therefore be transferred to the USA; under its addendum, Render
    relies on the EU-US Data Privacy Framework, with the EU Standard Contractual
    Clauses as a fallback.

    **How long it is kept.** The site keeps no request logs, and typed answers
    are discarded once checked. The application's error logs do not record
    visitors' IP addresses, and Render deletes them after 7 days.

    **Cookies and browser storage.** This site sets no cookies for visitors.
    While a page is open, it keeps two technical identifiers in your browser's
    session storage so that the page works; they are deleted when you close the
    tab. A login cookie is set only when the site administrator logs in.

    **Your rights.** You can ask for access to your data, its correction or
    erasure, or the restriction of its processing, by writing to
    {CONTACT_EMAIL}. You can also complain to the Spanish Data Protection
    Agency (AEPD), [www.aepd.es](https://www.aepd.es).

    **Right to object.** You may object at any time, on grounds relating to your
    particular situation, to processing based on legitimate interests, by writing
    to the same address.

    **Links to other sites.** Links to external learning resources lead to sites
    with their own privacy policies.
    """).strip()

PRIVACY_ES = dedent(f"""
    ## Aviso de privacidad

    Última actualización: {LAST_UPDATED_ES}

    **Responsable.** WES350, entrenadores multilingües de conjugación verbal, es
    un proyecto de portafolio gratuito y sin fines comerciales, gestionado por
    Yevhen Babko (GitHub: Yevguen), Málaga, España. Contacto: {CONTACT_EMAIL}.

    **Qué datos se tratan.**

    - Para servirle las páginas, el proveedor de alojamiento, Render, trata su
      dirección IP y datos técnicos de la solicitud, como la página solicitada.
      El propio sitio no guarda registros de las solicitudes de los visitantes.
    - Las respuestas que escribe en los entrenadores se envían al servidor solo
      para comprobarlas y mostrar las correcciones. No se guardan.
    - El sitio no tiene cuentas de visitantes: el registro público está cerrado.
      Las únicas cuentas son las del propio administrador del sitio.
    - No se usan herramientas de analítica, publicidad ni seguimiento, y no se
      venden ni se ceden datos con fines comerciales.
    - El sitio no adopta decisiones automatizadas, incluida la elaboración de
      perfiles, que produzcan efectos jurídicos o afecten de forma similar y
      significativa.

    Facilitar su dirección IP no es una obligación legal ni contractual, pero es
    técnicamente necesario para ofrecer el sitio; sin ella, no puede mostrarse.

    **Finalidad y base jurídica.** La base jurídica para ofrecer el sitio,
    comprobar las respuestas y utilizar los identificadores técnicos necesarios
    es mi interés legítimo en prestar un servicio que funcione y sea seguro y en
    resolver problemas (artículo 6.1.f del RGPD).

    **Quién más los trata.** Render Services, Inc. (San Francisco, EE. UU.) aloja
    el sitio conforme a su anexo de tratamiento de datos. Render también puede
    tratar ciertos datos de uso del servicio como responsable independiente,
    según su política de privacidad. Por ello, los datos pueden transferirse a
    EE. UU.; según su anexo, Render se basa en el Marco de Privacidad de Datos
    UE-EE. UU. y, en su defecto, en las cláusulas contractuales tipo de la UE.

    **Conservación.** El sitio no guarda registros de solicitudes, y las
    respuestas escritas se descartan una vez comprobadas. Los registros de
    errores de la aplicación no recogen las direcciones IP de los visitantes, y
    Render los elimina a los 7 días.

    **Cookies y almacenamiento del navegador.** Este sitio no instala cookies a
    los visitantes. Mientras una página está abierta, guarda dos identificadores
    técnicos en el almacenamiento de sesión del navegador para que la página
    funcione; se eliminan al cerrar la pestaña. Solo se instala una cookie de
    inicio de sesión cuando el administrador del sitio inicia sesión.

    **Sus derechos.** Puede solicitar el acceso a sus datos, su rectificación o
    supresión, o la limitación de su tratamiento, escribiendo a
    {CONTACT_EMAIL}. También puede presentar una reclamación ante la Agencia
    Española de Protección de Datos (AEPD), [www.aepd.es](https://www.aepd.es).

    **Derecho de oposición.** Puede oponerse en cualquier momento, por motivos
    relacionados con su situación particular, al tratamiento basado en intereses
    legítimos, escribiendo a la misma dirección.

    **Enlaces a otros sitios.** Los enlaces a recursos externos llevan a sitios
    con sus propias políticas de privacidad.
    """).strip()


@ui.page("/privacy")
def privacy_page() -> None:
    ui.button("⬅️ Back to Menu", on_click=lambda: ui.navigate.to("/"))
    for text in (PRIVACY_EN, PRIVACY_ES):
        with ui.card().classes("w-full max-w-2xl mx-auto my-4"):
            ui.markdown(text)
