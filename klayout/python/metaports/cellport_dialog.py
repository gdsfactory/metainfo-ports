import pya
from metaports.ports import shapes_shown, cell_toggle_ports_state

app = pya.Application.instance()
mw = app.main_window()

class PortMenu(pya.QDialog):
  """
  This class implements a dialog for showing or hiding ports per cell or for all
  """

  def __init__(self, parent = None):
    """ Dialog constructor """
    
    pya.QDialog.__init__(self)

    self.setWindowTitle("Show Ports")

    self.resize(640, 480)
    
    self.ly = pya.CellView.active().layout()

    layout = pya.QVBoxLayout(self)
    self.setLayout(layout)
    
    # Create an QHBoxLayout for buttons
    button_layout = pya.QHBoxLayout(self)

    # "Show All" button
    show_all_button = pya.QPushButton("Show All", self)
    show_all_button.clicked = self.show_all_items
    button_layout.addWidget(show_all_button)

    # Add a stretch to push buttons to the right
    button_layout.addStretch()

    # "Hide All" button
    hide_all_button = pya.QPushButton("Hide All", self)
    hide_all_button.clicked = self.hide_all_items
    button_layout.addWidget(hide_all_button)

    # Add the button layout to the main layout
    layout.addLayout(button_layout)
    
    self.table = pya.QTableWidget(self)
    self.table.setColumnCount(1)
    self.table.setHorizontalHeaderLabels(["Sow ports of cell"])
    self.table.verticalHeader.visible=False
    self.table.horizontalHeader.setSectionResizeMode(0, pya.QHeaderView_ResizeMode.Stretch)
    self.table.setSelectionMode(pya.QAbstractItemView.NoSelection)
    self.populate_table()
    self.table.itemChanged = self.item_changed
    layout.addWidget(self.table)
    
    btnbox = pya.QDialogButtonBox(self)
    btnbox.setStandardButtons(pya.QDialogButtonBox.Close)
    btnbox.rejected = self.close
    layout.addWidget(btnbox)
    
  def populate_table(self):
  
    cells = [c for c in self.ly.cells("*")]
    cells.sort(key=lambda cell: cell.name)
    
    lvx = mw.current_view_index
    idx = pya.CellView.active().index()
    
    if lvx not in shapes_shown:
      shapes_shown[lvx] = {idx: {}}
    elif idx not in shapes_shown[lvx]:
      shapes_shown[lvx][idx] = {}
    layout_shapes = shapes_shown[lvx][idx]
    
    for i, cell in enumerate(cells):
      self.table.insertRow(i)
      item = pya.QTableWidgetItem(cell.name)
      item.flags = item.flags & ~(pya.Qt.ItemFlag.ItemIsSelectable | pya.Qt.ItemFlag.ItemIsEditable)| pya.Qt.ItemFlag.ItemIsUserCheckable
      self.table.setItem(i, 0, item)
      #item.flags = (item.flags | pya.Qt.ItemFlag.ItemIsUserCheckable)# & ~(pya.Qt.ItemFlag.ItemIsSelectable | pya.Qt.ItemFlag.ItemIsEditable)
      item.setCheckState(pya.Qt.Checked if cell.cell_index() in layout_shapes else pya.Qt.Unchecked)
      

  def show_all_items(self):
      for row in range(self.table.rowCount):
          item = self.table.item(row, 0)
          if item:
              item.setCheckState(pya.Qt.Checked)

  def hide_all_items(self):
      for row in range(self.table.rowCount):
          item = self.table.item(row, 0)
          if item:
              item.setCheckState(pya.Qt.Unchecked)

  def item_changed(self, item):
    cell = self.ly.cell(item.text)
    lvx = mw.current_view_index
    idx = pya.CellView.active().index()
    cell_toggle_ports_state(lvx, idx, cell, item.checkState == pya.Qt.Checked)

