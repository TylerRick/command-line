/*
$Id: shed.c,v 1.15 2005/09/05 22:41:00 alexsisson Exp $

shed 1.12 source

(C) Copyright 2002-2005 Alex Sisson (alexs@cyberspace.org)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

/* includes */
#include <stdio.h>     /* fprintf    */
#include <ncurses.h>   /* ncurses    */
#include <signal.h>    /* signal     */
#include <string.h>    /* strcmp etc */
#include <stdlib.h>    /* exit       */
#include <sys/stat.h>  /* stat       */
#include <getopt.h>    /* getopt     */
#include <ctype.h>     /* tolower    */
#include <unistd.h>    /* dup, dup2  */

#include "util.h"

/* function prototypes */
void finish(int s);
void ctrlc(int s);
void cursorup(int n);
void cursordown(int n);
void cursorleft();
void cursorright();
int  cursorjump(int n);
void clearline(int line, int width);
int  search(char* str);
int  getinput(int emptystr);
int  mainloop(int getstrmode);
int  redraw();
int  dump(char *dumpfile);

/* globals */
char   *filename;
FILE   *f;
int    len           = 0;                               /* file length */
int    cursorx       = 0;                               /* offset of cursor from SOF */
int    cursory       = 0;                               /* which column cursor is in */
int    viewport      = 0;                               /* offset of current view from SOF */
int    viewsize      = 0;                               /* size of viewport */
int    decmode       = 1;                               /* dec or hex display */
int    ascmode       = 0;                               /* setting for ascii column */
int    readonly      = 0;                               /* readonly flag */
int    preview       = 0;                               /* preview mode on/off */
int    startoffset   = 0;                               /* arg of --start stored here */
int    offsetwidth   = 0;                               /* width of left column */
int    colbase[5]    = {0,16,10,8,2};                   /* base of each column */
int    colwidth[5]   = {1,2,3,3,8};                     /* width of columns */
int    coloffset[5]  = {0,6,10,14,18};                  /* offset from left for each column */
char   *coltitle[5]  = {"asc","hex","dec","oct","bin"}; /* name of each column */
char   *searchstr[5] = {0,0,0,0,0};                     /* previous searches */
char   *reply        = NULL;                            /* where input is returned */
int    fdin          = 0;                               /* for dup()'ed stdin */
fd_set fdset;                                           /* for select()ing fdin */
char   *stdinbuf     = NULL;                            /* buf for stdin */

#define STDINBUFSIZE 0xFFFF


/* main */
int main(int argc, char **argv) {

  int i;

  /* getopt long opts */
  struct option opts[] = { {"help",0,0,'h'},
                           {"version",0,0,'v'},
                           {"readonly",0,0,'r'},
                           {"start",1,0,'s'},
                           {0,0,0,0} };


  /* hack for getopt's error messages */
//  strcpy(argv[0],PACKAGE);
  argv[0] = strdup(PACKAGE);

  /* process args */
  while(1) {
    i = getopt_long(argc,argv,getopt_makeoptstring(opts),opts,0);
    if(i<0)
      break;
    switch(i) {
      case 'h':
        fprintf(stdout,"usage: %s [OPTIONS] [FILE]\n\n",PACKAGE);
        fprintf(stdout,"options:\n");
        fprintf(stdout,"  -r / --readonly       open FILE read only\n");
        fprintf(stdout,"  -s / --start=OFFSET   position cursor to offset\n");
        fprintf(stdout,"  -h / --help           show help and exit\n");
        fprintf(stdout,"  -v / --version        show version and exit\n");
        return 0;
      case 'v':
        fprintf(stdout,"%s %s\n",PACKAGE,VERSION);
        return 0;
      case 'r':
        readonly = 1;
        break;
      case 's':
        startoffset = atoi(optarg);
        break;
      case '?':
        return 1;
    }
  }

  /* open stream */
  switch(argc-optind) {

    case 1:
      /* non-option argument */
      if(argv[optind][0]!='-' || strlen(argv[optind])>1) {
        filename = argv[optind];
        if(!readonly)
          f = fopen(filename,"r+");
        if(readonly || !f) {
          f = fopen(filename,"r");
          if(!f) {
            fprintf(stderr,"%s: could not open %s\n",PACKAGE,filename);
            return 1;
          }
          readonly = 1;
        }
        /* stat file */
        struct stat st;
        if(stat(filename,&st)<0) {
          fprintf(stderr,"%s: could not stat %s - perhaps it is too big (>2Gb)\n",PACKAGE,filename);
          return 1;
        }
        if(S_ISDIR(st.st_mode)) {
          fprintf(stderr,"%s: %s is a directory\n",PACKAGE,filename);
          return 1;
        }
        len = st.st_size;
        fgetc(f);
        if(!len && feof(f)) {
          fprintf(stderr,"%s: %s has zero size\n",PACKAGE,filename);
          return 1;
        }
        break;
      }
      /* else drop through */

    case 0:
      /* reading from stdin */
      if(isatty(STDIN_FILENO)) {
        fprintf(stderr,"%s: input from stdin must be piped/redirected.\n",PACKAGE);
        return 1;
      }
      f = tmpfile();
      if(!f) {
        fprintf(stderr,"%s: tmpfile() failed.\n",PACKAGE);
        return 1;
      }
      readonly = 1;
      /* sort out fd's so we can still press keys */
      fdin = dup(STDIN_FILENO);
      dup2(STDOUT_FILENO,STDIN_FILENO);
      filename = "(stdin)";
      stdinbuf = malloc(STDINBUFSIZE);
 
    default:
      break;
  }

  /* init ncurses */
  signal(SIGINT,ctrlc);
  initscr();
  keypad(stdscr,TRUE);
  cbreak();
  noecho();
  halfdelay(1);

  /* set size of viewport to LINES - 6 (2 reservered for top + 4 for bottom area) */
  viewsize = LINES - 6;

  /* calculate the width for the offset column and round it */
  if(len) {
    offsetwidth = calcwidth(len,10);
    while(offsetwidth%4!=0)
      offsetwidth++;
  } else
    offsetwidth = 16;

  if(startoffset) {
    if(len && startoffset>len)
      startoffset = len-1;
    cursorjump(startoffset);
  }

  redraw();
  mainloop(0);

  return 0;
}

int mainloop(int getstrmode) {

  int i,key;

  while(1) {

    if(getstrmode) {

      key = getch();

      switch(key) {

        case 3:  /* ctrlc */
        case 27: /* esc */
          getstrmode = 0;
          return -1;

        case 127: /* bkspc */
        case 8:   /* ^H */
          if(strlen(reply)) {
            reply[strlen(reply)-1] = 0;
            mvaddch(stdscr->_cury,stdscr->_curx-1,' ');
            move(stdscr->_cury,stdscr->_curx-1);
          }
          break;

        case '\n':
          getstrmode = 0;
          return 0;

        default:
          if(isprint(key)) {
            reply[strlen(reply)] = key;
            addch(key);
            refresh();
          }
          break;

      }

    } else {

      if(fdin) {
        struct timeval tv = {0,0};
        FD_ZERO(&fdset);
        FD_SET(fdin,&fdset);
        if(select(fdin+1,&fdset,0,0,&tv)>0) {
          if(FD_ISSET(fdin,&fdset)) {
            i = read(fdin,stdinbuf,STDINBUFSIZE);
            if(i>0) {
              fseek(f,len,SEEK_SET);
              fwrite(stdinbuf,1,i,f);
              len += i;
            } else
              fdin = 0;
          }
        }
      }

      redraw();

      key = toupper(getch());

      switch(key) {

        case KEY_UP:
          cursorup(1);
          break;

        case KEY_DOWN:
          cursordown(1);
          break;

        case KEY_LEFT:
          cursorleft(1);
          break;

        case KEY_RIGHT:
        case 9: /* tab */
          cursorright(1);
          break;

        case KEY_PPAGE:
        case 25: /* ctrl Y */
          cursorup(16);
          break;

        case KEY_NPAGE:
        case 22: /* ctrl V */
          cursordown(16);
          break;

        case KEY_HOME:
        case 1: /* ctrl A */
          cursory = 0;
          break;

        case KEY_END:
        case 5: /* ctrl E */
          cursory = 4;
          break;

        /* edit */
        case ' ':
        case 'E':
          if(readonly) {
            beep();
            break;
          }
          clearerr(f);
          fseek(f,cursorx,SEEK_SET);
          attron(A_REVERSE);
          clearline(LINES-3,24);
          mvprintw(LINES-3,0,"new value (%s): ",coltitle[cursory]);
          getinput(0);
          attroff(A_REVERSE);
          if(!reply)
            break; /* input cancelled */
          if(!cursory)
            fputc((int)reply[0],f); /* first column */
          else {
            int l;
            l = parsestring(reply,colbase[cursory]);
            if(l<0 || l>255)
              break;
            fputc(l,f);
          }
          break;

        /* exit */
        case 'X':
        case 24:  /* ^X */
        case 27:  /* esc */
          finish(0);
          break;

        /* jump to */
        case 'J':
          attron(A_REVERSE);
          clearline(LINES-3,24);
          mvprintw(LINES-3,0,"jump to (%s): ",decmode?"dec":"hex");
          getinput(0);
          attroff(A_REVERSE);
          if(!reply)
            break;
          long target;
          if(strequ(reply,"top"))
            target = 0;
          else if(strequ(reply,"end")) {
            if(len)
              target = len - 1;
            else {
              target = cursorx;
              beep();
            }
          } else {
            target = parsestring(reply,decmode?10:16);
            if(target<0)
              break;
            if(len && target>=len)
              target = len-1;
          }
          cursorjump(target);
          break;

        /* repeat search */
        case 267: /* F3 */
        case 'R':
        case 'N':
          if(searchstr[cursory]) {
            search("");
            break;
          }

        case 'S':
        case 23: /* ^W */
        case 'W':
        case 'F':
        case '/':
          attron(A_REVERSE);
          clearline(LINES-3,24);
          mvprintw(LINES-3,0,"search for (%s)",coltitle[cursory]);
          if(searchstr[cursory])
            printw("[%s]",searchstr[cursory]);
          printw(": ");
          getinput(1);
          attroff(A_REVERSE);
          search(reply);
          break;

        /* toggle */
        case 'T':
          decmode = !decmode;
          break;

        /* ascii mode change */
        case 'A':
          ascmode++;
          if(ascmode>2)
            ascmode=0;
          break;

        /* preview */
        case 'P':
          preview = !preview;
          break;

        /* dump */
        case 'D':
          attron(A_REVERSE);
          clearline(LINES-3,COLS);
          mvaddstr(LINES-3,0,"dump to file: ");
          getinput(0);
          attroff(A_REVERSE);
          if(!reply)
            break;
          dump(reply);
          break;

        /* redraw */
        case 12: /* ^L */
          erase();
          refresh();
          break;

        /* resize */
        case KEY_RESIZE:
          refresh();
          viewsize = LINES - 6;
          if(cursorx>=viewport+viewsize)
            viewport = cursorx;
          if(viewport+viewsize>len) {
            while(viewport+viewsize>len)
              cursorup(1);
          }
          cursordown(viewsize);
          for(i=1;i<LINES-1;i++)
            clearline(i,COLS);
          refresh();
          break;

        default:
          break;
      }
    }
  }
  finish(0);
}



/* functions */

/* ends ncurses and quits */
void finish(int s) {
  endwin();
  printf("\n");
  exit(s);
}

/* handles ctrl c */
void ctrlc(int s) {
  ungetch(3);
}



/* cursor movements functions */
void cursorup(int n) {
  while(n--) {
    if(cursorx) {
      cursorx--;
      if(cursorx<viewport)
        viewport--;
    }
    else
      beep();
  }
}

void cursordown(int n) {
  while(n--) {
    if(cursorx<len-1 || !len) {
      cursorx++;
      if(cursorx>=viewport+viewsize)
        viewport++;
    }
    else
      beep();
  }
}

void cursorleft() {
  if(cursory)
    cursory--;
  else
   beep();
}

void cursorright() {
  if(cursory<4)
    cursory++;
  else
    beep();
}


/* clears a line on the screen */
void clearline(int line, int width) {
  move(line,0);
  while(width--)
    addch(' ');
}

/* search */
int search(char *str) {

  unsigned char c;
  int i,slen;
  unsigned char *search = NULL;
  long l;

  if(!str)
    return 0;

  if(strlen(str)) {
    /* user entered a string, so make a copy to searchstr for repeat searches. */
    free(searchstr[cursory]);
    searchstr[cursory] = strdup(str);
  } else if(!searchstr[cursory]) {
    /* else user just pressed enter, but no previous search */
    return 0;
  }

  slen = strlen(searchstr[cursory]);
  search = malloc(slen+2);
  strcpy(search,searchstr[cursory]);

  if(cursory) {
    char *p = malloc(slen+2);
    strcpy(p,search);
    p = strtok(p," :,.\0");
    for(i=0;p;i++) {
      l = parsestring(p,colbase[cursory]);
      if(l<0 || l>255)
        return 0;
      search[i] = (unsigned char)l;
      p = strtok(NULL," :,.\0");
    }
    free(p);
    search[i] = 0;
    slen = i;
  }

  cursordown(1);

  clearerr(f);
  fseek(f,cursorx,SEEK_SET);
  for(;cursorx<len-1;cursordown(1)) {
    c = fgetc(f);
    if(c==search[0]) {
      for(i=1;i<slen;i++) {
        c = fgetc(f);
        if(c!=search[i])
          break;
      }
      if(i==slen) {
        cursordown(i-1);
        cursorup(i-1);
        return 1;
      }
      clearerr(f);
      fseek(f,cursorx+1,SEEK_SET);
    }
  }

  free(search);
  return 0;
}

int cursorjump(int n) {

  if(cursorx>n) {
    if(n<viewport || n>viewport+viewsize) {
      cursorx = n;
      viewport = cursorx;
    } else
      cursorup(cursorx-n);
  } else {
    if(n<viewport || n>viewport+viewsize) {
      cursorx = n;
      viewport = cursorx - (viewsize - 1);
    } else
      cursordown(n-cursorx);
  }
  return 0;
}

int redraw() {

  int i,c;
  char str[256];

  /* redraw top */
  attron(A_REVERSE);
  clearline(0,COLS);
  mvprintw(0,0,"%s%s",filename,readonly?" (read only)":"");
  mvprintw(0,COLS-9,"shed %s",VERSION);
  attroff(A_REVERSE);

  /* draw column headers */
  mvaddstr(1,0,(offsetwidth==4)?"offs":"offset");
  mvaddstr(1,offsetwidth+2,"asc hex dec oct bin");

  /* seek to current part of file and display */
  clearerr(f);
  for(i=0;i<viewsize;i++) {
    fseek(f,viewport+i,SEEK_SET);
    c = fgetc(f);
    if(c<0)
      break;
    mvprintw(i+2,0,"%s: ",getstring(viewport+i,str,(decmode)?10:16,offsetwidth));
    printw("%s ",getascii(c,str,ascmode));
    printw("%s  ",getstring(c,str,16,2));
    printw("%s ",getstring(c,str,10,3));
    printw("%s ",getstring(c,str, 8,3));
    printw("%s ",getstring(c,str, 2,8));
    c = offsetwidth+coloffset[4]+9;
    move(i+2,c);
    for(;c<COLS;c++)
      addch(' ');
  }

  /* draw cursor */
  clearerr(f);
  fseek(f,cursorx,SEEK_SET);
  c = fgetc(f);
  attron(A_REVERSE);
  int pos = (cursorx - viewport) + 2;
  if(!cursory)
    mvaddch(pos,offsetwidth+3,(c>32&&c<127)?c:' ');
  else
    mvaddstr(pos,offsetwidth+coloffset[cursory],getstring(c,str,colbase[cursory],colwidth[cursory]));
  attroff(A_REVERSE);

  /* draw preview */
  if(preview) {
    i = offsetwidth+coloffset[4]+9;
    move(pos,i);
    for(;i<COLS||i<16;i++) {
      addch(c>=32 && c<=127 ? c : ' ');
      c = fgetc(f);
      if(c<0||c=='\n')
        break;
    }
  }

  /* draw cursor pos */
  attron(A_REVERSE);
  clearline(LINES-3,COLS);
  if(cursorx==len-1)
    mvaddstr(LINES-3,0,"(end)");
  c = decmode?10:16;
  mvaddstr(LINES-3,COLS-(calcwidth(cursorx,c)+calcwidth(len,c)+8),getstring(cursorx,str,c,0));
  addstr("/");
  addstr(getstring(len,str,c,0));
  addstr((decmode)?" (dec)":" (hex)");
  attroff(A_REVERSE);

  /* draw key help */
  clearline(LINES-2,COLS);
  clearline(LINES-1,COLS);
  mvaddstr(LINES-2,0,"SPACE|E edit  S|W|F search  J jump to       T toggle dec/hex  D dump");
  mvaddstr(LINES-1,0,"X       exit  R|N   repeat  A extended asc  P preview");
  mvaddstr(LINES-1,COLS-1," ");
  refresh();

  return 0;
}

int getinput(int emptystr) {
  free(reply);
  reply = malloc(128);
  if(!reply)
    return -1;
  memset(reply,0,128);
  if(!mainloop(1))
    if(emptystr||strlen(reply))
      return 0;  
  free(reply);
  reply = NULL;
  return -1;
}

int dump(char *dumpfile) {

  int i,c;
  FILE *df;
  char str[32];

  df = fopen(reply,"w");
  if(!df)
    return -1;

  attron(A_REVERSE);
  mvaddstr(LINES-3,0,"dumping...");
  mvprintw(LINES-3,11+offsetwidth,"/%s",getstring(len,str,decmode?10:16,offsetwidth));

  fprintf(df,"%s%s",((offsetwidth==4)?"offs":"offset"),"  asc hex dec oct bin\n");
  rewind(f);
  for(i=0;i<len;i++) {
    c = fgetc(f);
    if(c<0)
      break;
    if(!(i%1024)) {
      mvaddstr(LINES-3,11,getstring(i,str,decmode?10:16,offsetwidth));
      refresh();
    }
    fprintf(df,"%s:  ",getstring(viewport+i,str,decmode?10:16,offsetwidth));
    fprintf(df,"%c  ",(char)((c>32&&c<127)?c:' '));
    fprintf(df,"%s  ",getstring(c,str,16,2));
    fprintf(df,"%s ",getstring(c,str,10,3));
    fprintf(df,"%s ",getstring(c,str, 8,3));
    fprintf(df,"%s\n",getstring(c,str, 2,8));
  }
  attroff(A_REVERSE);
  fclose(df);
  return 0;
}
