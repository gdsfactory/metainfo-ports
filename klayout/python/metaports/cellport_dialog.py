# $description: Cell Port Dialog Widget
import pya
from metaports.ports import shapes_shown, cell_toggle_ports_state, get_all_port_types, get_selected_port_types, set_selected_port_types

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
    self.lvx = mw.current_view_index
    self.idx = pya.CellView.active().index()

    layout = pya.QVBoxLayout(self)
    self.setLayout(layout)
    
    # Port type filter section
    port_type_group = pya.QGroupBox("Filter by Port Type", self)
    port_type_layout = pya.QVBoxLayout(port_type_group)
    port_type_group.setLayout(port_type_layout)
    
    # Get all available port types from the layout
    self.available_port_types = get_all_port_types(self.ly)
    self.port_type_checkboxes = {}
    
    # Get currently selected port types (if any)
    current_selection = get_selected_port_types(self.lvx, self.idx)
    
    # Create checkboxes for each port type
    port_type_checkbox_layout = pya.QHBoxLayout()
    for port_type in self.available_port_types:
      checkbox = pya.QCheckBox(port_type, port_type_group)
      # If no selection exists, check all by default
      if current_selection is None or port_type in current_selection:
        checkbox.setChecked(True)
      else:
        checkbox.setChecked(False)
      checkbox.stateChanged = self.on_port_type_filter_changed
      self.port_type_checkboxes[port_type] = checkbox
      port_type_checkbox_layout.addWidget(checkbox)
    
    port_type_checkbox_layout.addStretch()
    port_type_layout.addLayout(port_type_checkbox_layout)
    
    # Add select all / deselect all buttons for port types
    port_type_btn_layout = pya.QHBoxLayout()
    select_all_types_btn = pya.QPushButton("Select All Types", port_type_group)
    select_all_types_btn.clicked = self.select_all_port_types
    port_type_btn_layout.addWidget(select_all_types_btn)
    
    deselect_all_types_btn = pya.QPushButton("Deselect All Types", port_type_group)
    deselect_all_types_btn.clicked = self.deselect_all_port_types
    port_type_btn_layout.addWidget(deselect_all_types_btn)
    port_type_btn_layout.addStretch()
    port_type_layout.addLayout(port_type_btn_layout)
    
    layout.addWidget(port_type_group)
    
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
    self.table.setHorizontalHeaderLabels(["Show ports of cell"])
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
  
  def get_selected_port_types_from_ui(self):
    """Get currently selected port types from the UI checkboxes."""
    # Always return a set; an empty set means "hide all types", while
    # None is reserved elsewhere as the sentinel for "no filter / show all".
    selected = set()
    for port_type, checkbox in self.port_type_checkboxes.items():
      if checkbox.isChecked():
        selected.add(port_type)
    return selected
  
  def on_port_type_filter_changed(self, state):
    """Handle port type filter checkbox changes."""
    selected_types = self.get_selected_port_types_from_ui()
    set_selected_port_types(self.lvx, self.idx, selected_types)
    self.refresh_visible_ports()
  
  def _set_all_port_types_checked(self, checked):
    """Helper to (de)select all port type checkboxes efficiently."""
    # Temporarily block signals to avoid N calls to refresh_visible_ports()
    for checkbox in self.port_type_checkboxes.values():
      checkbox.blockSignals(True)
      checkbox.setChecked(checked)
    # Re-enable signals after all checkboxes have been updated
    for checkbox in self.port_type_checkboxes.values():
      checkbox.blockSignals(False)
    # Now apply the changes once
    selected_types = self.get_selected_port_types_from_ui()
    set_selected_port_types(self.lvx, self.idx, selected_types)
    self.refresh_visible_ports()
  
  def select_all_port_types(self):
    """Select all port type checkboxes."""
    self._set_all_port_types_checked(True)
  
  def deselect_all_port_types(self):
    """Deselect all port type checkboxes."""
    self._set_all_port_types_checked(False)
  
  def refresh_visible_ports(self):
    """Refresh visible ports based on current filter settings."""
    selected_types = self.get_selected_port_types_from_ui()
    
    # Get all cells that currently have ports shown
    if self.lvx in shapes_shown and self.idx in shapes_shown[self.lvx]:
      cells_with_ports = list(shapes_shown[self.lvx][self.idx].keys())
      # Hide all current ports and re-show with new filter
      for cidx in cells_with_ports:
        cell = self.ly.cell(cidx)
        if cell:
          # First hide
          cell_toggle_ports_state(self.lvx, self.idx, cell, False)
          # Then show with new filter
          cell_toggle_ports_state(self.lvx, self.idx, cell, True, selected_types)
    
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
    selected_types = self.get_selected_port_types_from_ui()
    cell_toggle_ports_state(lvx, idx, cell, item.checkState == pya.Qt.Checked, selected_types)

