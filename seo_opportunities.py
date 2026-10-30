"""Prioritize query-level Search Console exports using explicit scenario assumptions."""

import argparse
import csv
import math
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Query:
    query: str
    clicks: int
    impressions: int
    position: float

    @property
    def ctr(self):
        return self.clicks / self.impressions if self.impressions else 0.0


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.strip().lower())
                   if not unicodedata.combining(c))


ALIASES = {
    'query': {'query', 'queries', 'top queries', 'consulta', 'consultas', 'consultas principales'},
    'clicks': {'clicks', 'clics'},
    'impressions': {'impressions', 'impresiones'},
    'position': {'position', 'average position', 'posicion', 'posicion media'},
}


def load_queries(path):
    """Read UTF-8 comma/semicolon CSV. Reject ambiguous or invalid datasets."""
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        sample = handle.read(8192)
        handle.seek(0)
        if not sample.strip():
            raise ValueError('El CSV está vacío.')
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error as error:
            raise ValueError('No se reconoce el delimitador del CSV.') from error
        reader = csv.DictReader(handle, dialect=dialect)
        fields = reader.fieldnames or []
        mapping = {}
        for canonical, aliases in ALIASES.items():
            matches = [field for field in fields if normalized(field) in aliases]
            if len(matches) != 1:
                raise ValueError(f'Se necesita exactamente una columna {canonical}.')
            mapping[canonical] = matches[0]
        result, seen = [], set()
        for line, row in enumerate(reader, 2):
            try:
                query = row[mapping['query']].strip()
                clicks = int(row[mapping['clicks']])
                impressions = int(row[mapping['impressions']])
                position = float(row[mapping['position']].replace(',', '.'))
                if not query or clicks < 0 or impressions < 0 or clicks > impressions:
                    raise ValueError('Consulta vacía o recuentos incoherentes.')
                if not math.isfinite(position) or position < 1:
                    raise ValueError('La posición debe ser finita y >= 1.')
                if query in seen:
                    raise ValueError('Consulta duplicada: exporta una sola fila por consulta.')
                seen.add(query)
                result.append(Query(query, clicks, impressions, position))
            except (ValueError, TypeError, AttributeError) as error:
                raise ValueError(f'Fila {line}: {error}') from error
        if not result:
            raise ValueError('El CSV no contiene consultas.')
        return result


def rank_queries(queries, min_impressions=100, min_position=4, max_position=20,
                 target_ctr=0.05, exclude=()):
    """Compute scenario click gaps, not forecasts or a universal SEO score."""
    if min_impressions < 1 or not (1 <= min_position <= max_position < math.inf):
        raise ValueError('Rango de posiciones o mínimo de impresiones inválido.')
    if not (0 < target_ctr <= 1):
        raise ValueError('El CTR objetivo debe ser mayor que 0 y como máximo 1.')
    excluded = [normalized(term) for term in exclude if term.strip()]
    rows = []
    for item in queries:
        if item.impressions < min_impressions or not min_position <= item.position <= max_position:
            continue
        if any(term in normalized(item.query) for term in excluded):
            continue
        gap = item.impressions * target_ctr - item.clicks
        if gap <= 0:
            continue
        rows.append({'query': item.query, 'clicks': item.clicks,
                     'impressions': item.impressions, 'position': item.position,
                     'ctr': round(item.ctr, 6), 'scenario_target_ctr': target_ctr,
                     'scenario_click_gap': round(gap, 2),
                     'review': 'Revisar intención, página asociada y SERP antes de actuar'})
    return sorted(rows, key=lambda row: (-row['scenario_click_gap'], row['query']))


FIELDS = ['query', 'clicks', 'impressions', 'position', 'ctr',
          'scenario_target_ctr', 'scenario_click_gap', 'review']


def spreadsheet_safe(value):
    # Prevent exported queries from being interpreted as spreadsheet formulas.
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, default=Path('opportunities.csv'))
    parser.add_argument('--min-impressions', type=int, default=100)
    parser.add_argument('--min-position', type=float, default=4)
    parser.add_argument('--max-position', type=float, default=20)
    parser.add_argument('--target-ctr', type=float, default=0.05,
                        help='Hipótesis decimal, no benchmark. 0.05 = 5%%.')
    parser.add_argument('--exclude', action='append', default=[],
                        help='Excluir consultas que contengan este texto; repetible.')
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('La salida no puede sobrescribir la entrada.')
        queries = load_queries(args.input)
        rows = rank_queries(queries, args.min_impressions, args.min_position,
                            args.max_position, args.target_ctr, args.exclude)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation protects prior reports from accidental overwrites.
        with args.output.open('x', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows({k: spreadsheet_safe(v) for k, v in row.items()} for row in rows)
    except (OSError, ValueError, csv.Error) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    print(f'{len(rows)} oportunidades de {len(queries)} consultas -> {args.output}')
    print('La brecha de clics es un escenario, no una predicción de tráfico.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
