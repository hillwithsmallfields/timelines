#!/usr/bin/python3

import argparse
import csv
import datetime
import os.path

PREFER_LEFTMOST = True          # if false, tries to re-use the column last occupied furthest back (doesn't work yet)

this_year = datetime.date.today().year

class Interval():

    def __init__(self, begin, end, subject, area):
        self.begin = begin
        self.end = end
        self.subject = subject
        self.area = area
        self.rowspan = 1

    def __str__(self):
        return "<from %d to %d: %s (%s) rs=%d>" % (self.begin, self.end,
                                                   self.subject, self.area,
                                                   self.rowspan)

class TimeLines():

    def __init__(self):
        self.columns = []
        self.years = []         # all the years in which an interval starts
        self.next_year = {}     # maps each element of self.years to the next one
        self.earliest_year = 1000000
        self.latest_year = -self.earliest_year

    def add_data(self, rowsource):
        for row in rowsource:
            self.add_row(row)

    def add_row(self, row):
        if row['Begin date'] == "":
            return
        begin = int(row['Begin date'])
        raw_end = row['End date']
        end = (this_year
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
            if latest < begin and PREFER_LEFTMOST or end < earliest_end:
                best_column = colno
                earliest_end = end
        if best_column:
            self.columns[best_column].append(interval)
        else:
            self.columns.append([interval])

    def fill_in_gaps(self):
        """Put filler intervals in the gaps in each column."""
        for column in self.columns:
            if column[0].begin < self.earliest_year:
                self.earliest_year = column[0].begin
            if column[0].end > self.latest_year:
                self.latest_year = column[0].end
        # gapstring = "<!-- empty -->"
        # gapstring = ""
        gapstring = "[gap]"
        for i, column in enumerate(self.columns):
            filled_column = []
            gap_start = self.earliest_year
            # first filler is from earliest time to start of this column
            for interval in column:
                if interval.begin > gap_start:
                    filled_column.append(Interval(gap_start+1, interval.begin-1, gapstring, ""))
                filled_column.append(interval)
                gap_start = interval.end
            # last filler is from end of this column until now
            if filled_column[-1].end < self.latest_year:
                filled_column.append(Interval(filled_column[-1].end+1, self.latest_year, gapstring, ""))
            self.columns[i] = filled_column

    def find_start_years(self):
        years = set()
        for column in self.columns:
            for interval in column:
                years.add(interval.begin)
        self.years = sorted(years)
        self.next_year = {}
        prev_year = self.earliest_year
        for year in self.years:
            self.next_year[prev_year] = year
            prev_year = year
        self.next_year[self.years[-1]] = self.latest_year

    def set_rowspans(self):
        for column in self.columns:
            for interval in column:
                this_year = interval.begin
                while this_year < interval.end and this_year < self.latest_year:
                    interval.rowspan += 1
                    this_year = self.next_year[this_year]
                interval.rowspan -= 1

    def output_HTML(self, filename):
        cursors = [0] * len(self.columns)
        with open(filename, 'w') as outstream:
            outstream.write('<html>\n  <head>\n    <title>Timelines</title>\n  </head>\n  <body>\n')
            outstream.write('    <table border="1">\n')
            for year in self.years:
                outstream.write('      <tr><th>%d</th>\n' % year)
                for i, column in enumerate(self.columns):
                    c = cursors[i]
                    if c >= len(column):
                        continue
                    cell = column[c]
                    if cell.begin == year:
                        outstream.write('      <td rowspan="%d" valign="top">%s' % (cell.rowspan, cell.subject))
                        if True:
                            outstream.write("<br>(%d -- %d)" % (cell.begin, cell.end))
                        outstream.write('</td>\n')
                        cursors[i] += 1
                outstream.write('      </tr>\n')
            outstream.write('  </table>')
            outstream.write('  </body>\n</html>\n')

    def output_SVG(self, filename):
        with open(filename, 'w') as outstream:
            pass                # TODO: write this

    def dump_raw(self):
        for colno, coldata in enumerate(self.columns):
            print("column", colno)
            for interval in coldata:
                print("  ", interval)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="+",
                        help="""Input files (CSV)""")
    parser.add_argument("-o", "--output",
                        help="""Output file""")
    args = parser.parse_args()

    timelines = TimeLines()

    for filename in args.input:
        with open(filename) as instream:
            reader = csv.DictReader(instream)
            timelines.add_data(reader)

    output = args.output or os.path.splitext(args.input[0])[0] + ".html"

    if output.endswith(".html"):
        timelines.fill_in_gaps()
        timelines.find_start_years()
        timelines.set_rowspans()
        # timelines.dump_raw()
        timelines.output_HTML(output)
    elif output.endswith(".svg"):
        timelines.output_SVG(output)
    else:
        print("I don't know how to write that kind of output.")

if __name__ == "__main__":
    main()
