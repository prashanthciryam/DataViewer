#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 15:50:15 2023

@author: prashanthciryam
"""

import sys
import os
import pandas as pd
import re
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio import SeqIO
from pyteomics import mass, parser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QTabWidget, QLineEdit, QVBoxLayout, QWidget, QFileDialog, QAbstractItemView,
    QComboBox, QCheckBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QSize
import uuid
from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    finished = pyqtSignal(object, str)  # Signal to indicate the thread has finished
    
    def __init__(self, func, records, tab_name):
        super().__init__()
        self.func = func
        self.records = records
        self.tab_name = tab_name
    
    def run(self):
        result = self.func(self.records)
        self.finished.emit(result,self.tab_name)

class DataViewerApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None

    def init_ui(self):
        self.setWindowTitle('Data Viewer')
        
        # Get screen size to make the window 1/3 of the screen size
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        self.resize(int(screen_size.width() // 1.5), int(screen_size.height() // 1.5))
        
        self.df_dict = {}
        self.records_dict = {}
        self.uid_dict = {}

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        #Create a horizontal layout for search bar
        self.setup_search_bar()
        self.layout.addLayout(self.search_layout)
        
        # Create a horizontal layout for table and some buttons
        self.horizontal_layout = QHBoxLayout()
        
        self.setup_table_tabs()
        
        # Create a grid layout for export/import buttons
        self.gridLayoutWidget = QWidget()  # Create a QWidget for the grid layout
        self.gridLayoutWidget.setMaximumSize(QSize(230, 230))  # Set maximum size for the grid
        self.grid_layout = QGridLayout(self.gridLayoutWidget)
        self.grid_layout.setSpacing(5)
        
        self.create_button('Import CSV', self.import_csv, layout=self.grid_layout, position=(0, 0), size=(100, 100))
        self.create_button('Export CSV', self.export_csv, layout=self.grid_layout, position=(0, 1), size=(100, 100))
        self.create_button('Import FASTA', self.import_fasta, layout=self.grid_layout, position=(1, 0), size=(100, 100))
        self.create_button('Export FASTA', self.export_fasta, layout=self.grid_layout, position=(1, 1), size=(100, 100))
        
        # Add table and grid to the horizontal layout
        self.horizontal_layout.addWidget(self.table_tabs)
        self.horizontal_layout.addWidget(self.gridLayoutWidget)
        
        # Add the horizontal layout to the main layout
        self.layout.addLayout(self.horizontal_layout)
        
        # Create a vertical layout for other buttons
        self.vertical_layout = QVBoxLayout()
        self.create_button('Generate tryptic peptides', self.display_tryptic_peptides, layout=self.vertical_layout)
        self.create_button('Generate m/z', self.display_mass_charge, layout=self.vertical_layout)
        
        # Add the vertical layout to the main layout
        self.layout.addLayout(self.vertical_layout)
        
        self.init_empty_table()
    
    def reset_column_selector(self):
        if not self.table_tabs.currentWidget():
            self.column_selector.clear()
            self.column_selector.addItem("All")
        else:
            uid = self.table_tabs.currentWidget().property('uid')
            self.df = self.df_dict[uid]
            if isinstance(self.df,pd.DataFrame):
                self.column_selector.clear()
                self.column_selector.addItem("All")
                for col in self.df.columns:
                    self.column_selector.addItem(col)
            

    def setup_search_bar(self):
        # Define the search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Find...")
        self.search_bar.textChanged.connect(self.search_text)
        
        # Define the replace bar
        self.replace_bar = QLineEdit(self)
        self.replace_bar.setPlaceholderText("Replace with...")
        self.replace_bar.hide()  # Hide by default
        
        # Define the column selector
        self.column_selector = QComboBox(self)
        self.column_selector.addItem("All")  # Default
        
        # Making the search bar sufficiently wide
        self.search_bar.setMinimumWidth(200)
        self.replace_bar.setMinimumWidth(200)
        
        # Find/Replace Toggle Button
        self.toggle_replace_button = QCheckBox("Find/Replace", self)
        self.toggle_replace_button.toggled.connect(self.toggle_replace_mode)
        
        # Define the 'Confirm Replace' button
        self.confirm_replace_button = QPushButton("Confirm", self)
        self.confirm_replace_button.clicked.connect(self.confirm_replace)
        
        # Define the 'Use Regex' checkbox
        self.use_regex_checkbox = QCheckBox("Use Regex")
        
        
        # Organize widgets
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_bar)
        self.search_layout.addWidget(self.replace_bar)
        self.search_layout.addWidget(self.column_selector)
        self.search_layout.addWidget(self.toggle_replace_button)
        self.search_layout.addWidget(self.confirm_replace_button)  # Add this button to the layout
        self.search_layout.addWidget(self.use_regex_checkbox)
    
    def toggle_replace_mode(self, toggled):
        if toggled:
            self.replace_bar.show()
        else:
            self.replace_bar.hide()


    def setup_table_tabs(self):
        self.table_tabs = QTabWidget()
        self.table_tabs.setTabsClosable(True)
        self.table_tabs.tabCloseRequested.connect(self.close_tab)
        self.layout.addWidget(self.table_tabs)
        self.table_tabs.currentChanged.connect(self.reset_column_selector)

    def create_button(self, label, handler, layout=None, position=None, size=None):
        button = QPushButton(label, self)
        button.clicked.connect(handler)
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        if size:
            button.setMinimumSize(QSize(size[0], size[1]))  # Set the minimum size
    
        if layout is None:
            self.layout.addWidget(button)
        elif isinstance(layout, QGridLayout):
            layout.addWidget(button, position[0], position[1])
        elif isinstance(layout, QVBoxLayout):
            layout.addWidget(button)

    def init_empty_table(self):
        empty_df = pd.DataFrame()
        self.show_dataframe(empty_df, 'Initial Empty Table')
    
    def rebuild_uid_dict(self):
        self.uid_dict = {}
        for index in range(self.table_tabs.count()):
            tab = self.table_tabs.widget(index)
            uid = tab.property('uid')
            self.uid_dict[index] = uid

    def close_tab(self, index):
        tab = self.table_tabs.widget(index)
        uid = tab.property('uid')
        del self.df_dict[uid]
        if uid in self.records_dict:
            del self.records_dict[uid]
        self.table_tabs.removeTab(index)
        self.rebuild_uid_dict()
        
    def get_tab_index_from_uid(self, uid):
        for index, tab_uid in self.uid_dict.items():
            if tab_uid == uid:
                return index
        return None
    
    def confirm_replace(self):
        if not self.replace_bar.text():
            self.filter_results()
        else:
            find_text = self.search_bar.text()
            
            # If "Use Regex" is not checked, escape the find_text
            if not self.use_regex_checkbox.isChecked():
                find_text = re.escape(find_text)
            
            replace_text = self.replace_bar.text()
            current_uid = self.table_tabs.currentWidget().property('uid')
            current_df = self.df_dict.get(current_uid, pd.DataFrame())
            if not current_df.empty:
                current_df.replace(to_replace=find_text, value=replace_text, inplace=True, regex=True)
                self.show_dataframe(current_df, "Modified Table")


  
    def import_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open CSV File', '', 'CSV files (*.csv)')
        if file_name:
            df = pd.read_csv(file_name)
            self.show_dataframe(df,os.path.basename(file_name))
    
    def import_fasta(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open FASTA File', '', 'FASTA files (*.fasta)')
        df, records = self.fastaToDF(file_name)
        if file_name:   
            uid = self.show_dataframe(df,os.path.basename(file_name))
            self.records_dict[uid] = records  # Store the records in records_dict
            
    def generateAllTrypticPeptides(self,records):
        tryptic = []
        for record in records:
            temp = self.trypticPeps(record)
            tryptic+=temp
        return tryptic
    
    def trypticPeps(self,record):
        peptide = str(record.seq)
        n,i,d = record.name,record.id,record.description
        tryptic_peptides = list(parser.cleave(peptide,parser.expasy_rules['trypsin'], 0))
        x=1
        records = []
        for pep in tryptic_peptides:
            new_record = SeqRecord(Seq(pep),\
            id=i,\
            name=n,
            description=d+' Fragment %s' % x)
            records.append(new_record)
            x+=1
        return records
    
    def recordsToDF(self,records):
        preprocess = []
        for record in records:
            temp = {'Name':str(record.name),\
                   'ID':str(record.id),\
                   'Description':str(record.description).replace('\t','; '),\
                   'Sequence':str(record.seq)}
            preprocess.append(temp)
        df = pd.DataFrame(preprocess)
        return df
    
    def display_tryptic_peptides(self):
        current_uid = self.table_tabs.currentWidget().property('uid')
        if current_uid in self.records_dict:
            current_index = self.table_tabs.currentIndex()
            tab_name = self.table_tabs.tabText(current_index)
            records = self.records_dict[current_uid]
            
            # Create a worker object and connect signals
            self.worker = Worker(self.generateAllTrypticPeptides, records, tab_name)
            self.worker.finished.connect(self.on_tryptic_worker_finished)
            self.worker.start()
    
    def on_tryptic_worker_finished(self, tryptic, tab_name):
        df = self.recordsToDF(tryptic)
        uid = self.show_dataframe(df, tab_name+" Tryptic Peptides")
        self.records_dict[uid] = tryptic
    
    
    
    def export_csv(self):
        current_uid = self.table_tabs.currentWidget().property('uid')
        df = self.df_dict[current_uid]
        current_index = self.table_tabs.currentIndex()
        tab_name = self.table_tabs.tabText(current_index).replace(' ','_').replace(':','')
        
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save CSV As...', tab_name, '.csv')
        df.to_csv(file_name,index=False)
    
    def export_fasta(self):
        current_uid = self.table_tabs.currentWidget().property('uid')
        if current_uid in self.records_dict:
            records = self.records_dict[current_uid]
            current_index = self.table_tabs.currentIndex()
            tab_name = self.table_tabs.tabText(current_index).replace(' ','_').replace(':','')
        
            file_name, _ = QFileDialog.getSaveFileName(self, 'Save FASTA As...',tab_name,'.fasta')
            SeqIO.write(records,file_name,'fasta')
            return None
        return None
    
    def display_mass_charge(self):
        current_index = self.table_tabs.currentIndex()
        tab_name = self.table_tabs.tabText(current_index)
        if tab_name:
            current_uid = self.table_tabs.currentWidget().property('uid')
            new_name = tab_name.strip(' Tryptic Peptides')
            peps = self.records_dict[current_uid]
            # audit,df = self.mass_charge(peps)
            self.worker = Worker(self.mass_charge, peps, new_name)
            self.worker.finished.connect(self.on_mz_worker_finished)
            self.worker.start()
    
    def mass_charge(self,pepList):
        # to_df1 = []
        to_df2 = []
        for pep in pepList:
            try:
                sequence = str(pep.seq)
            except(AttributeError):
                print(pep)
                sequence = ''
            if len(sequence)<6 or 'X' in sequence:
                continue
            else:
                m = mass.fast_mass(sequence,charge = 1)
                record2 = {'Compound': sequence,\
                         'Formula': '',\
                         'M': m,\
                         'z range': ' 2-5'}
                # to_df1.append(record1)
                to_df2.append(record2)
        # df1 = pd.DataFrame(to_df1)
        df2 = pd.DataFrame(to_df2)
        # return df1,df2
        return df2
    
    def on_mz_worker_finished(self, df, tab_name):
        uid = self.show_dataframe(df,tab_name+' Thermo Ready')
        return uid
    
    def filteredFASTA(self, df):
        records = []
        for i,row in df.iterrows():
            temp = SeqRecord(name = str(row['Name']),\
                             id = str(row['ID']),\
                                 description = str(row['Description']),\
                                     seq = Seq(str(row['Sequence'])))
            records.append(temp)
        print(records[0])
        return records
    
    def filter_results(self):
        query = self.search_bar.text()
        current_uid = self.table_tabs.currentWidget().property('uid')
        current_df = self.df_dict.get(current_uid, pd.DataFrame())
        current_index = self.table_tabs.currentIndex()
        tab_name = self.table_tabs.tabText(current_index)

        if not current_df.empty:
            mask = current_df.applymap(lambda x: bool(re.search(query, str(x))) if pd.notnull(x) else False)
            filtered_df = current_df[mask.any(axis=1)]
            uid = self.show_dataframe(filtered_df, tab_name+" Filtered: "+query)
            if current_uid in self.records_dict:
                filtfasta = self.filteredFASTA(filtered_df)
                self.records_dict[uid] = filtfasta

    def fastaToDF(self, fasta_file):
        records = list(SeqIO.parse(fasta_file, 'fasta'))
        preprocess = []
        for record in records:
            temp = {'Name': str(record.name), \
                    'ID': str(record.id), \
                    'Description': str(record.description).replace('\t', '; '), \
                    'Sequence': str(record.seq)}
            preprocess.append(temp)
        df = pd.DataFrame(preprocess)
        return df, records

    def show_dataframe(self, df, tab_name):
        tab = QTableWidget()
        tab.setColumnCount(len(df.columns))
        tab.setHorizontalHeaderLabels(df.columns)
        tab.setRowCount(len(df.index))
        tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tab.setSortingEnabled(True)
        
        current_index = self.table_tabs.currentIndex()
        if not self.table_tabs.currentWidget():
            current_df = pd.DataFrame(['foo'])
        else:
            current_uid = self.table_tabs.currentWidget().property('uid')
            current_df = self.df_dict.get(current_uid,pd.DataFrame)
            
        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                tab.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
        uid = str(uuid.uuid4())
        tab.setProperty('uid', uid)
        self.uid_dict[self.table_tabs.count()] = uid
        self.df_dict[uid] = df     
        
        new_tab_index = self.table_tabs.addTab(tab, tab_name)
        self.rebuild_uid_dict()
        self.table_tabs.setCurrentIndex(new_tab_index)
        if current_df.empty:    
            self.close_tab(current_index)
            return uid
        else:
            return uid

    def search_text(self):
        query = self.search_bar.text()
        selected_column = self.column_selector.currentText()  # Get the selected column
        current_tab = self.table_tabs.currentWidget()
    
        # If query is empty, remove all highlighting and return
        if not query:
            if current_tab:
                for i in range(current_tab.rowCount()):
                    for j in range(current_tab.columnCount()):
                        item = current_tab.item(i, j)
                        if item:
                            item.setBackground(QColor(255, 255, 255))  # White to remove highlighting
            return
    
        if current_tab:
            for i in range(current_tab.rowCount()):
                for j in range(current_tab.columnCount()):
                    # Skip columns that don't match the selected column, if one is selected
                    if selected_column != "All" and current_tab.horizontalHeaderItem(j).text() != selected_column:
                        continue
                    
                    item = current_tab.item(i, j)
                    if item:
                        item_text = item.text()
                        try:
                            if re.search(query, item_text):
                                start = item_text.find(query)
                                end = start + len(query)
                                # TODO: Highlight only the matched substring here
                                item.setBackground(QColor(255, 255, 0))  # Yellow for highlighting
                            else:
                                item.setBackground(QColor(255, 255, 255))  # White to remove highlighting
                        except re.error:
                            pass  # Invalid regex; do nothing



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataViewerApp()
    window.show()
    sys.exit(app.exec_())