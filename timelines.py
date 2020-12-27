#!/usr/bin/python3

import argparse
import csv
import datetime
import os.path

PREFER_LEFTMOST = True          # if false, tries to re-use the column last occupied furthest back (doesn't work yet)

year_chart_produced = datetime.date.today().year

class Interval():

    def __init__(self, begin, end, subject, area):
        self.begin = begin
        self.end = end
        self.subject = subject
        self.area = area
        self.rowspan = 1

    def __str__(self):
        return "<from %d to %d: %s (%s) spans %d rows>" % (self.begin, self.end,
                                                   self.subject, self.area,
                                                   self.rowspan)

class TimeLines():

    def __init__(self):
        self.columns = []
        self.years = []         # all the years in which an interval starts
        self.next_year = {}     # maps each element of self.years to the next one
        self.earliest_year = 1000000
        self.latest_year = -self.earliest_year
        self.extended = False
        self.show_gaps = False
        self.gapstring = "[gap]"

    def add_data(self, rowsource):
        for row in rowsource:
            self.add_row(row)

    def add_row(self, row):
        if row['Begin date'] == "":
            return
        begin = int(row['Begin date'])
        raw_end = row['End date']
        end = ((year_chart_produced if self.extended else begin)
               if raw_end == '*'
               else (begin
                     if (raw_end == '.' or raw_end == "")
                     else int(raw_end)))
        interval = Interval(begin, end,
                            row['Subject'], row['Area'])
        if not self.columns:
            self.columns.append([interval])
            return
        earliest_end = self.columns[0][-1].end
        best_column = None
        for colno, coldata in enumerate(self.columns):
            latest = coldata[-1].end
            if latest < begin and (PREFER_LEFTMOST or end < earliest_end):
                best_column = colno
                earliest_end = end
        if best_column is not None:
            self.columns[best_column].append(interval)
        else:
            self.columns.append([interval])

    def fill_in_gaps(self):
        """Put filler intervals in the gaps in each column."""
        for column in self.columns:
            if column[0].begin < self.earliest_year:
                self.earliest_year = column[0].begin
            if column[-1].end > self.latest_year:
                self.latest_year = column[-1].end
        for i, column in enumerate(self.columns):
            print("filling gaps in column", i)
            filled_column = []
            gap_start = self.earliest_year
            # first filler is from earliest time to start of this column
            for interval in column:
                print("  interval", interval)
                if interval.begin > gap_start:
                    print("  adding gap before interval, from", gap_start, "to", interval.begin-1)
                    filled_column.append(Interval(gap_start, interval.begin-1, self.gapstring, ""))
                filled_column.append(interval)
                gap_start = interval.end + 1
            # last filler is from end of this column until now
            # print("  column", i, "ends with", filled_column[-1].subject, "at", filled_column[-1].end, "and the table ends at", self.latest_year)
            if filled_column[-1].end < self.latest_year:
                filled_column.append(Interval(filled_column[-1].end+1, self.latest_year, self.gapstring, ""))
            self.columns[i] = filled_column

    def find_start_years(self):
        years = set()
        for column in self.columns:
            for interval in column:
                years.add(interval.begin)
                years.add(interval.end) # TODO: I think I need to do this too, but maybe it should be end-1?
        self.years = sorted(years)
        self.next_year = {}
        prev_year = self.earliest_year
        for year in self.years:
            self.next_year[prev_year] = year
            prev_year = year
        self.next_year[self.years[-1]] = self.latest_year

    def set_rowspans(self):
        for i, column in enumerate(self.columns):
            for interval in column:
                this_year = interval.begin
                # the next year in which anything starts in any column:

                # TODO: this seems to be wrong; cells are getting two many rows; it might be to do with whether there are year entries for years in which something finishes but nothing starts
                
                next_year = self.next_year[this_year]
                while next_year < interval.end and this_year <= self.latest_year:
                    print("Stretching column", i, "interval", interval)
                    interval.rowspan += 1
                    this_year = next_year
                    next_year = self.next_year.get(this_year, self.latest_year+1)

    def output_HTML(self, filename):
        cursors = [0] * len(self.columns)
        with open(filename, 'w') as outstream:
            outstream.write('<html>\n  <head>\n    <title>Timelines</title>\n  </head>\n  <body>\n')
            outstream.write('    <table border="1">\n')
            for year in self.years:
                empty = True
                for i, column in enumerate(self.columns):
                    c = cursors[i]
                    if c >= len(column):
                        continue
                    cell = column[c]
                    if cell.begin == year:
                        if self.show_gaps or cell.subject != self.gapstring or c + 1 == len(column):
                            if empty:
                                outstream.write('      <tr><th>%d</th>\n' % year)
                                empty = False
                            outstream.write('        <td rowspan="%d" valign="top">%s' % (cell.rowspan, cell.subject))
                            if cell.begin == cell.end:
                                outstream.write("<br>(%d)" % cell.begin)
                            else:
                                outstream.write("<br>(%d -- %d)" % (cell.begin, cell.end))
                            if True:
                                outstream.write("<br>{%d}" % i)
                        outstream.write('</td>\n')
                        cursors[i] += 1
                if not empty:
                    outstream.write('      </tr>\n')
            outstream.write('  </table>\n')
            outstream.write('  </body>\n</html>\n')

    def output_SVG(self, filename):
        with open(filename, 'w') as outstream:
            pass                # TODO: write this

    def dump_raw(self, title):
        print(title)
        for colno, coldata in enumerate(self.columns):
            print("  column", colno)
            for interval in coldata:
                print("    ", interval)

    def dump_by_years(self, title):
        print(title)
        cursors = [0] * len(self.columns)
        for year in self.years:
            print("  Year", year)
            empty = True
            for i, column in enumerate(self.columns):
                c = cursors[i]
                if c >= len(column):
                    continue
                cell = column[c]
                if cell.begin == year:
                    print("    column", i, "begins", cell.subject, "continuing to", cell.end)
                    cursors[i] += 1
                    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="+",
                        help="""Input files (CSV)""")
    parser.add_argument("-o", "--output",
                        help="""Output file""")
    parser.add_argument("-x", "--extended",
                        help="""Open-ended intervals extend to now""")
    parser.add_argument("-d", "--debug", action='store_true')
    args = parser.parse_args()

    timelines = TimeLines()

    if args.extended:
        timelines.extended = True
    
    for filename in args.input:
        with open(filename) as instream:
            reader = csv.DictReader(instream)
            timelines.add_data(reader)

    output = args.output or os.path.splitext(args.input[0])[0] + ".html"

    if output.endswith(".html"):
        if args.debug:
            timelines.dump_raw("As read")
        timelines.fill_in_gaps()
        if args.debug:
            timelines.dump_raw("With gaps filled in")
        timelines.find_start_years()
        timelines.set_rowspans()
        if args.debug:
            timelines.dump_raw("With rowspans")
            timelines.dump_by_years("As assembled")
        timelines.output_HTML(output)
    elif output.endswith(".svg"):
        timelines.output_SVG(output)
    else:
        print("I don't know how to write that kind of output.")

if __name__ == "__main__":
    main()
