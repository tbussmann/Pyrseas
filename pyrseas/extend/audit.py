# -*- coding: utf-8 -*-
"""
    pyrseas.extend.audit
    ~~~~~~~~~~~~~~~~~~~~

    This module defines two classes: CfgAuditColumn derived from
    DbExtension and CfgAuditColumnDict derived from DbExtensionDict.
"""
from pyrseas.extend import DbExtension, DbExtensionDict
from pyrseas.dbobject import split_schema_obj


CFG_AUDIT_COLUMNS = \
    {
    'default': {
            'columns': ['modified_by_user', 'modified_timestamp'],
            'triggers': ['audit_columns_default']
            },
    'created_date_only': {
            'columns': ['created_date']
            }
    }


class CfgAuditColumn(DbExtension):
    """An extension that adds automatically maintained audit columns"""

    keylist = ['name']

    def apply(self, table, extdb):
        """Apply configuration audit columns to argument table.

        :param table: table to which columns/triggers will be added
        :param extdb: extension dictionaries
        """
        currdb = extdb.current
        sch = table.schema
        for col in self.columns:
            extdb.columns[col].apply(table)
        if hasattr(self, 'triggers'):
            for trg in self.triggers:
                extdb.triggers[trg].apply(table)
                for newtrg in table.triggers:
                    fncsig = table.triggers[newtrg].procedure
                    fnc = fncsig[:fncsig.find('(')]
                    (sch, fnc) = split_schema_obj(fnc)
                    if (sch, fncsig) not in currdb.functions:
                        newfunc = extdb.functions[fnc].apply(
                            sch, extdb.columns.col_trans_tbl, extdb)
                        # add new function to the current db
                        extdb.add_func(sch, newfunc)
                        extdb.add_lang(newfunc.language)


class CfgAuditColumnDict(DbExtensionDict):
    "The collection of audit column extensions"

    cls = CfgAuditColumn

    def __init__(self):
        for aud in CFG_AUDIT_COLUMNS:
            self[aud] = CfgAuditColumn(name=aud, **CFG_AUDIT_COLUMNS[aud])

    def from_map(self, inaudcols):
        """Initalize the dictionary of functions by converting the input map

        :param inaudcols: YAML map defining the audit column configuration
        """
        for aud in list(inaudcols.keys()):
            audcol = CfgAuditColumn(name=aud)
            for attr in list(inaudcols[aud].keys()):
                if attr == 'columns':
                    audcol.columns = [col for col in inaudcols[aud][attr]]
                elif attr == 'triggers':
                    audcol.triggers = {}
                    for trg in list(inaudcols[aud][attr].keys()):
                        audcol.triggers.update(inaudcols[aud][attr][trg])
            self[audcol.name] = audcol
