# -*- coding: utf-8 -*-
from src.eralchemy.models import Table, Relation, Column


class ParsingException(Exception):
    base_traceback = 'Error on line {line_nb}: {line}\n{error}'
    hint = None

    @property
    def traceback(self):
        rv = self.base_traceback.format(
            line_nb=getattr(self, 'line_nb', '?'),
            line=getattr(self, 'line', ''),
            error=self.args[0],
        )
        if self.hint is not None:
            rv += '\nHINT: {}'.format(self.hint)
        return rv


class DuplicateTableException(ParsingException):
    pass


class DuplicateColumnException(ParsingException):
    pass


class RelationNoColException(ParsingException):
    hint = 'Try to declare the tables before the relationships.'


class NoCurrentTableException(ParsingException):
    hint = 'Try to declare the tables before the relationships and columns.'


class ERAlchemyLineParseError(ParsingException):
    pass


def remove_comments_from_line(line):
    if '#' not in line:
        return line.strip()
    return line[:line.index('#')].strip()


def _check_no_current_table(new_obj, current_table):
    """ Raises exception if we try to add a relation or a column
    with no current table. """
    if current_table is None:
        msg = 'Cannot add {} before adding table'
        if isinstance(new_obj, Relation):
            raise NoCurrentTableException(msg.format('relation'))
        if isinstance(new_obj, Column):
            raise NoCurrentTableException(msg.format('column'))


def _update_check_inputs(current_table, tables, relations):
    assert current_table is None or isinstance(current_table, Table)
    assert isinstance(tables, list)
    assert all(isinstance(t, Table) for t in tables)
    assert all(isinstance(r, Relation) for r in relations)
    assert current_table is None or current_table in tables


def _check_colname_in_lst(column_name, columns_names):
    if column_name not in columns_names:
        msg = 'Cannot add a relation with column "{}" which is undefined'
        raise RelationNoColException(msg.format(column_name))


def _check_not_creating_duplicates(new_name,names, type, exc):
    if new_name in names:
        msg = 'Cannot add {} named "{}" which is ' \
              'already present in the schema.'
        raise exc(msg.format(type, new_name))


def update_models(new_obj, current_table, tables, relations):
    """ Update the state of the parsing. """
    _update_check_inputs(current_table, tables, relations)
    _check_no_current_table(new_obj, current_table)

    if isinstance(new_obj, Table):
        _check_not_creating_duplicates(new_obj.name, (t.name for t in tables), 'table', DuplicateTableException)
        return new_obj, tables + [new_obj], relations

    if isinstance(new_obj, Relation):
        tables_names = tuple(t.name for t in tables)
        _check_colname_in_lst(new_obj.right_col, tables_names)
        _check_colname_in_lst(new_obj.left_col, tables_names)
        return current_table, tables, relations + [new_obj]

    if isinstance(new_obj, Column):
        columns_names = [c.name for c in current_table.columns]
        _check_not_creating_duplicates(new_obj.name, columns_names, 'column', DuplicateColumnException)
        current_table.columns.append(new_obj)
        return current_table, tables, relations

    msg = "new_obj cannot be of type {}"
    raise ValueError(msg.format(new_obj.__class__.__name__))


def markdown_file_to_intermediary(filename):
    """ Parse a file and return to intermediary syntax. """
    with open(filename) as f:
        lines = f.readlines()
    return line_iterator_to_intermediary(lines)


def line_iterator_to_intermediary(line_iterator):
    """ Parse an iterator of str (one string per line) to the intermediary syntax"""
    def parse_line():
        for typ in [Table, Relation, Column]:
            match = typ.RE.match(line)
            if match:
                return typ.make_from_match(match)
        msg = f'Line "{line}" could not be parsed to an object.'
        raise ERAlchemyLineParseError(msg)

    def filter_lines_from_comments():
        """ Filter the lines from comments and non code lines. """
        for line_nb, raw_line in enumerate(line_iterator):
            clean_line = remove_comments_from_line(raw_line)
            if clean_line:
                yield line_nb, clean_line, raw_line

    current_table = None
    tables = []
    relations = []
    errors = []
    for line_nb, line, raw_line in filter_lines_from_comments():
        try:
            new_obj = parse_line()
            current_table, tables, relations = update_models(new_obj, current_table, tables, relations)
        except ParsingException as e:
            e.line_nb = line_nb
            e.line = raw_line
            errors.append(e)
    if len(errors) != 0:
        msg = 'ERAlchemy couldn\'t complete the generation due the {} following errors'.format(len(errors))
        raise ParsingException(msg + '\n\n'.join(e.traceback for e in errors))
    return tables, relations
