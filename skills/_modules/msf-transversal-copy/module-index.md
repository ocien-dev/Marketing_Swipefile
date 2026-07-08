# MSF Transversal Copy Modules

Status: `approved`

These modules are shared retrieval and playbook fragments for the first
process-skill wave. They are not standalone skills and must not be invoked as
independent process outputs.

## Modules

| module_id | import_as | process_tag | file |
|---|---|---|---|
| mecanismo-big-idea | `transversal:mecanismo-big-idea` | `process-mecanismo-big-idea` | `modules/mecanismo-big-idea.md` |
| prova-depoimentos | `transversal:prova-depoimentos` | `process-prova-depoimentos` | `modules/prova-depoimentos.md` |

## Import Rule

Process skills S03-S07 may import these modules by reference in their
`SKILL.md` and `retrieval.md`. Do not copy the module playbook into each
skill. The consuming skill should state:

```text
Imported transversal modules:
- transversal:mecanismo-big-idea -> skills/_modules/msf-transversal-copy/modules/mecanismo-big-idea.md
- transversal:prova-depoimentos -> skills/_modules/msf-transversal-copy/modules/prova-depoimentos.md
```

If a process skill needs only one module, import only that module.

## Owner Audit Gate

These modules can feed S03-S07 only after owner audit. Until then, keep S04 and
the rest of the first-wave skills blocked.
