from . import (
    search,
    filters,
    pagination,
    modal,
    dosage,
    dual_task,
    studies,
    time,
    download,
    views,
)

def register_callbacks(app):
    search.register(app)
    filters.register(app)
    pagination.register(app)
    modal.register(app)
    dosage.register(app)
    dual_task.register(app)
    studies.register(app)
    time.register(app)
    download.register(app)
    views.register(app)