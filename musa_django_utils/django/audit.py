import json
from contextvars import ContextVar

from asgiref.sync import sync_to_async
from django.db import connection, transaction

# Contexto da operação atual — async-safe via ContextVar
_audit_context: ContextVar[dict | None] = ContextVar('_audit_context', default=None)


def set_audit_context(data: dict) -> None:
    """
    Registra o contexto de auditoria para a operação atual.

    Em requests HTTP: chamado automaticamente pelo authenticate().
    Em jobs/scripts: chamar manualmente antes de usar audit_atomic().

    Exemplo:
        set_audit_context({
            'type': 'job',
            'user': None,
            'meta': {'task': 'issue_manifest', 'triggered_by': 'cron'},
        })
    """
    _audit_context.set(data)


def emit_audit_context() -> None:
    """Emite o contexto via pg_logical_emit_message dentro da transação ativa."""
    ctx = _audit_context.get()
    if not ctx:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_logical_emit_message(true, 'context', %s)",
            [json.dumps(ctx)],
        )


def clear_audit_context() -> None:
    _audit_context.set(None)


class audit_atomic:
    """
    Drop-in para transaction.atomic() que emite o contexto de auditoria
    automaticamente ao entrar na transação mais externa.

    Blocos aninhados criam SAVEPOINTs sem emitir novamente.
    Rollback remove o contexto do WAL (transactional=true).
    Funciona para sync (with) e async (async with).

    Uso em views async:
        async with audit_atomic():
            await Model.objects.acreate(...)

    Uso em management commands:
        set_audit_context({'type': 'job', 'meta': {'task': 'process_receipts'}})
        with audit_atomic():
            Model.objects.filter(...).update(...)

    Uso em scripts:
        set_audit_context({
            'type': 'script',
            'user': {'id': 'user@musa.co', 'username': 'user@musa.co', 'name': 'User'},
            'meta': {'script': 'fix_credentials'},
        })
        with audit_atomic():
            ReceiverMTR.objects.filter(...).update(...)
    """

    def __init__(self, using=None):
        self._atomic = transaction.atomic(using=using)
        self._is_outermost = False

    def _enter(self) -> None:
        # Se já havia transação ativa antes de entrar, é um SAVEPOINT — não emite
        self._is_outermost = not connection.in_atomic_block

    def _emit(self) -> None:
        if self._is_outermost:
            emit_audit_context()

    async def _aemit(self) -> None:
        if self._is_outermost:
            await sync_to_async(emit_audit_context)()

    # ------------------------------------------------------------------ sync
    def __enter__(self):
        self._enter()
        result = self._atomic.__enter__()
        self._emit()
        return result

    def __exit__(self, *args):
        return self._atomic.__exit__(*args)

    # ----------------------------------------------------------------- async
    async def __aenter__(self):
        self._enter()
        result = await self._atomic.__aenter__()
        await self._aemit()
        return result

    async def __aexit__(self, *args):
        return await self._atomic.__aexit__(*args)
