from fpdf import FPDF
from itertools import permutations
import datetime
import yaml
import io
import sys

class Note:
    NOTE_NAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    SCALE_LEN = len(NOTE_NAMES)
    MAJ_SCALE_STEPS = [2, 2, 1, 2, 2, 2, 1]
    MODIFIERS = ['b','#']
    SEMI_TONE_LEN = 12

    def __init__(self, name):
        self.note = None
        self.semi = None
        self.mod = None
        self.octave = None

        index = 0
        name = name.strip()
        self.note = self.NOTE_NAMES.index(name[index])
        index = index + 1
        while len(name) > index:
            if name[index].lower() == 'b':
                self.mod = 0
            elif name[index] == '#':
                self.mod = 1
            elif name[index].isdigit():
                self.octave = int(name[index])
            else:
                break
            index = index + 1

        self.semi = 0
        for i in range(self.note):
            self.semi = self.semi + self.MAJ_SCALE_STEPS[i]
        if self.mod == 0:
            self.semi = self.semi - 1
        if self.mod == 1:
            self.semi = self.semi + 1
            

    def __repr__(self):
        r = ""
        r = self.NOTE_NAMES[self.note]
        if self.mod != None:
            r = r + self.MODIFIERS[self.mod]
        if self.octave != None:
            r = r + str(self.octave)
        return r

    def distance(self, m, no_oct = True):
        ns = self.semi
        ms = m.semi

        if ns > ms:
            ms = ms + self.SEMI_TONE_LEN

        return ms - ns

class Ints:
    UN = 0
    m2 = 1
    M2 = 2
    m3 = 3
    M3 = 4
    P4 = 5
    TT = 6
    P5 = 7
    m6 = 8
    M6 = 9
    m7 = 10
    M7 = 11
    OCT = 12

    INTERVAL_NAMES = ["UNISON", "Minor Second", "Major Second", "Minor Third",
                      "Major Third", "Perfect Fourth", "Tritone", "Perfect Fifth",
                      "Minor Sixth", "Major Sixth", "Minor Seventh", "Major Seventh", "Octave"]



class Chord:
    THIRDS_DIST = [3,4,6,7,8,10,11]

    def name(self):
        return self.name_
    
    def _name(self):
        name = str(self.notes[0])
        if self.has_seventh():
            if self.has_third():
                if self.has_fifth():
                    if self.int_map[Ints.m7]:
                        if self.int_map[Ints.m3]:
                            if self.int_map[Ints.TT]:
                                name = name + "min7b5"
                            else:
                                name = name + "min7"
                        else:
                            name = name + "7"
                    else:
                        name = name + "Maj7"
        return name
                    
            

    def has_seventh(self):
        return self.int_map[Ints.m7] or self.int_map[Ints.M7]

    def has_third(self):
        return self.int_map[Ints.m3] or self.int_map[Ints.M3]

    def has_fifth(self):
        return self.int_map[Ints.TT] or self.int_map[Ints.P5]

    def set_interval_map(self):
        for i in self.dist_map[0]:
            self.int_map[i] = True

    def __repr__(self):
        return self.name()

    def root(self):
        return notes[0]

    def __init__(self, notes):
        self.int_map = [False]*12
        self.notes = []
        self.dist_map = []
        self.name_ = None
        notes = notes.split()
        for n in notes:
            self.notes.append(Note(n))
        self.distance_map()
        self.determine_root()
        self.set_interval_map()
        self.name_ = self._name()
    
    def determine_root(self):
        max_third_count = -1
        max_third_index = -1

        index = 0
        for r in self.dist_map:
            third_count = 0
            for d in r:
                if d in self.THIRDS_DIST:
                    third_count = third_count + 1
            if third_count > max_third_count:
                max_third_count = third_count
                max_third_index = index
            index = index + 1

        root = self.notes[max_third_index]
        self.notes.sort(key= lambda x: root.distance(x))
        self.distance_map()
        
    def distance_map(self):
        self.dist_map = []
        for n in self.notes:
            row = []
            self.dist_map.append(row)
            for m in self.notes:
                row.append(n.distance(m))

    def root(self):
        return self.notes[0]
    
    def intervals(self):
        invs = []
        index = 0
        for i in self.notes:
            if index != 0:
                invs.append(Ints.INTERVAL_NAMES[self.root().distance(i)])
            index = index + 1
        return invs

class Grid:

    STRINGS = 6
    FRETS = 7

    def __init__(self):
        self.tab = [None] * Grid.STRINGS
        for i in range(Grid.STRINGS):
            self.tab[i] = [0] * Grid.FRETS

        self.open_string = [None] * Grid.STRINGS
        self.fret_no = [None] * Grid.FRETS
        self.chord = None
        self.name = None

    def set_note(self, string, fret, order):
        if order == -1:
            order = 16
        self.tab[string][fret] = self.tab[string][fret] | (1 << order)

    def set_fret(self, fret, fret_no):
        self.fret_no[fret] = fret_no

    def set_open_string(self, string, order):
        self.open_string[string] = order

    def draw_x(self, pdf, x, y, w, h):
        pdf.set_draw_color(100)
        pdf.set_line_width(0.3)
        pdf.line(x,y,x+w,y+h)
        pdf.line(x,y+h,x+w,y)
        pdf.set_draw_color(0)

    def draw_triangle(self, pdf, x, y, w, h):
        pdf.set_draw_color(100)        
        pdf.set_line_width(0.3)
        pdf.line(x+w/2,y,x,y+h)
        pdf.line(x+w/2,y,x+w,y+h)
        pdf.line(x,y+h,x+w,y+h)
        pdf.set_draw_color(0)

    def draw_square(self, pdf, x, y, w, h):
        pdf.set_draw_color(100)
        pdf.set_line_width(0.3)
        pdf.line(x,y,x+w,y)
        pdf.line(x,y+h,x+w,y+h)
        pdf.line(x,y,x,y+h)
        pdf.line(x+w,y,x+w,y+h)
        pdf.set_draw_color(0)           

    def draw_circle(self, pdf, x, y, w, h, open=True):
        pdf.set_line_width(0.3)
        pdf.ellipse(x,y,w,h,style= 'D' if open else 'DF')

    def print_grid(self, pdf, x, y, w, h, section=None, divider=False):
        BORDER = 5
        TOP = 8
        BOTTOM = 3

        #pdf.rect(x, y, w, h)
        pdf.set_line_width(0.0)

        #strings
        dw = (w-2*BORDER)/(Grid.STRINGS-1)
        for i in range(Grid.STRINGS):
            pdf.line(x+BORDER+dw*i, y + TOP, x+BORDER+dw*i , y + h - BOTTOM)

        #frets
        dh = (h - TOP - BOTTOM) / (Grid.FRETS-1)
        for i in range(Grid.FRETS):
            pdf.line(x+BORDER, y + TOP + i * dh, x + w - BORDER , y + TOP + i * dh)

        #fret number
        for i in range(Grid.FRETS):
            pdf.set_font('Arial', '', 7)
            if self.fret_no[i] != None:
                pdf.set_xy(x+BORDER-4,y + TOP + i * dh)
                pdf.cell(4, dh, align='R', txt=str(self.fret_no[i]), border=0)


        #notes
        wo = 1.4
        ho = 1.4
        wob = wo+0.7 # need to make secondary objects bigger to show up over circle where necessary
        hob = ho+0.7
        
        for s in range(Grid.STRINGS):
            for f in range(Grid.FRETS):
                if self.tab[s][f] & (1 << 0) != 0: # filled circle
                    self.draw_circle(pdf, x+BORDER+dw*s-(wo/2),y + TOP + f * dh + dh/2 - ho/2 , wo, ho, open=False)
                if self.tab[s][f] & (1 << 16) != 0: # open circle
                    self.draw_circle(pdf, x+BORDER+dw*s-(wo/2),y + TOP + f * dh + dh/2 - ho/2 , wo, ho, open=True)
                if self.tab[s][f] & (1 << 1) != 0: # draw x
                    self.draw_x(pdf, x+BORDER+dw*s-(wob/2), y + TOP + f * dh + dh/2 - hob/2 , wob, hob)
                if self.tab[s][f] & (1 << 2) != 0: # draw triangle
                    self.draw_triangle(pdf, x+BORDER+dw*s-(wob/2), y + TOP + f * dh + dh/2 - hob/2 , wob, hob)
                if self.tab[s][f] & (1 << 3) != 0: # draw square
                    self.draw_square(pdf, x+BORDER+dw*s-(wob/2), y + TOP + f * dh + dh/2 - hob/2 , wob, hob)

        #open strings
        for s in range(Grid.STRINGS):
            if self.open_string[s] != None:
                pdf.ellipse(x+BORDER+dw*s-(wo/2),y + TOP + (-1) * dh + dh/2 - ho/2 , wo, ho, style='D')     


        #name
        if self.name != None:
            pdf.set_font('Arial', 'B', 8)
            pdf.set_xy(x,y)
            pdf.cell(w, TOP, align='C', txt=self.name, border=0)            

        #section
        SPACER = 0.3
        TOP_SPACE = 2
        if section != None:
            pdf.set_font('Arial', 'B', 8)
            pdf.set_xy(x-2,y)
            pdf.cell(2*2, TOP/2, align='L', txt=section, border=1)
        if divider:
            pdf.line(x-SPACER, y+TOP+TOP_SPACE, x-SPACER, y+h-BOTTOM-TOP_SPACE)
            pdf.line(x+SPACER, y+TOP+TOP_SPACE, x+SPACER, y+h-BOTTOM-TOP_SPACE)



class Song:

    def __init__(self):
        self.title = None
        self.composer = None
        self.arranger = None
        self.grids = []

    def print_title(self, pdf):
        pdf.set_xy(0.0,0.0)
        pdf.set_font('Arial', 'BU', 16)
        #pdf.set_text_color(220, 50, 50)
        pdf.cell(w=210.0, h=28.0, align='C', txt=self.title, border=0)

    def print_legend(self, pdf):
        pdf.set_xy(10.0,0.0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(w=50.0, h=15.0, align='L', txt='PLAY ', border=0)
        
        g = Grid()
        g.draw_circle(pdf, 22, 6.3, 2, 2, False)
        pdf.line(25.5, 7.3, 27.5, 7.3) 
        g.draw_x(pdf, 29, 6.3, 2, 2)
        pdf.line(32.5, 7.3, 34.5, 7.3) 
        g.draw_triangle(pdf, 36, 6.3, 2, 2)
        pdf.line(39.5, 7.3, 41.5, 7.3) 
        g.draw_square(pdf, 43, 6.3, 2, 2)
        
        
    def print_composer(self, pdf):
        if self.composer != None:
            pdf.set_xy(0.0,0.0)
            pdf.set_font('Arial', '', 12)
            #pdf.set_text_color(220, 50, 50)
            pdf.cell(w=210.0, h=40.0, align='C', txt=self.composer, border=0)

    def print_arranger(self, pdf):
        if self.arranger != None:
            currentDateTime = datetime.datetime.now()
            date = currentDateTime.date()
            year = date.strftime("%Y")

            pdf.set_xy(0.0,0.0)
            pdf.set_font('Arial', '', 10)
            #pdf.set_text_color(220, 50, 50)
            pdf.cell(w=200.0, h=15.0, align='R', txt='(ARR. '+self.arranger.upper()+' '+str(year)+')', border=0)
        
    def print_borders(self, pdf):
        pdf.set_line_width(0.0)
        pdf.line(5.0,5.0,205.0,5.0) # top one
        pdf.line(5.0,292.0,205.0,292.0) # bottom one
        pdf.line(5.0,5.0,5.0,292.0) # left one
        pdf.line(205.0,5.0,205.0,292.0) # right one

        pdf.rect(5.0, 5.0, 200.0,287.0)
        pdf.rect(8.0, 8.0, 194.0,282.0)


    def print_grids(self, pdf, w, h):
        BORDER = 10
        TOP = 30
        BOTTOM = 20
        ITEMS_PER_LINE = 8
        ITEMS_PER_ROW = 8

        full_index = 0
        index = 0
        line_no = 0
        
        cur_marker = 0 
        
        for grid in self.grids:
            if (index != 0) and (index % (ITEMS_PER_LINE * ITEMS_PER_ROW) == 0):
                #print("adding page")
                pdf.add_page()
                index = 0

            section = None
            divider = False

            if cur_marker < len(self.section_markers):
                sm = self.section_markers[cur_marker]
                if sm[0] == full_index:
                    section = sm[1]
                    divider = True
                    cur_marker = cur_marker + 1
            
            wg = (w - 2 * BORDER) / ITEMS_PER_LINE
            hg = (h - TOP - BOTTOM) / ITEMS_PER_ROW
            x = (index % ITEMS_PER_LINE) * wg + BORDER
            y = (int(index / ITEMS_PER_LINE)) * hg + TOP

            grid.print_grid(pdf, x, y, wg, hg, section, divider)
            index = index + 1
            full_index = full_index + 1

    def print_pdf(self,pdf_dir):
        pdf_w=210
        pdf_h=297
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        #self.print_borders(pdf)
        self.print_title(pdf)
        self.print_composer(pdf)
        self.print_arranger(pdf)
        self.print_legend(pdf)
        self.print_grids(pdf, pdf_w, pdf_h)
        

        pdf.set_author(self.arranger)
        
        pdf.output(pdf_dir+'/'+self.title + '.pdf','F')

    def load(self, name):
        with open(name, 'r') as stream:
            d = yaml.safe_load(stream)
            
            self.title = d['title']
            self.composer = d['composer']
            self.arranger = d['arranger']
            self.section_markers = []
            index = 0
            for dg in d['grids']:
                if 'section' in dg:
                    #print(dg['section'])
                    self.section_markers.append([index,dg['section']])
                else:
                    g = Grid()
                    g.name = dg['name']
                    for n in dg['tab']:
                        g.set_note(n[0],n[1],n[2])
                        g.set_fret(dg['fret'][0], dg['fret'][1])
                        if 'open strings' in dg:
                            for o in dg['open strings']:
                                g.set_open_string(o[0], o[1])
                    self.grids.append(g)
                    index = index + 1

            
def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: chords.py <yaml> <pdf-dir>')
        sys.exit(-1)

    yaml = sys.argv[1]
    pdf_dir = sys.argv[2] if len(sys.argv) == 3 else None
    song = Song()
    song.load(yaml)
    song.print_pdf(pdf_dir)

if __name__ == "__main__":
    main()
