"""
Devil ERP — Billing / POS Screen
Developed by Devil One Pvt Ltd & Nexuzy Lab
Lead Developer: David K. Angel
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QFrame, QMessageBox, QHeaderView, QDoubleSpinBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from billing.invoice_manager import InvoiceManager
from billing.gst_calculator import GSTCalculator
from billing.payment_handler import PaymentHandler
from billing.thermal_printer import ThermalPrinter
from inventory.inventory_manager import InventoryManager


class BillingScreen(QWidget):
    def __init__(self, user: dict = None, parent=None):
        super().__init__(parent)
        self.user = user or {}
        self.invoice_mgr = InvoiceManager()
        self.gst_calc    = GSTCalculator()
        self.pay_handler = PaymentHandler()
        self.inv_mgr     = InventoryManager()
        self.printer     = ThermalPrinter()
        self.cart        = []
        self._build_ui()

    # ── UI Build ─────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # LEFT — Cart
        left = QVBoxLayout()
        lbl = QLabel("🧾  New Bill / POS")
        lbl.setStyleSheet("color:#e0e0e0; font-size:16px; font-weight:bold;")
        left.addWidget(lbl)

        # Product search bar
        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search product by name or barcode...")
        self.search_box.setStyleSheet(self._input_style())
        self.search_box.returnPressed.connect(self._add_by_search)
        search_row.addWidget(self.search_box)
        add_btn = QPushButton("+ Add")
        add_btn.setStyleSheet(self._btn_style("#2196F3"))
        add_btn.clicked.connect(self._add_by_search)
        search_row.addWidget(add_btn)
        left.addLayout(search_row)

        # Cart table
        self.cart_table = QTableWidget(0, 6)
        self.cart_table.setHorizontalHeaderLabels(
            ["Product", "HSN", "Qty", "Rate", "GST%", "Total"]
        )
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setStyleSheet("""
            QTableWidget { background:#1a1a2e; color:#e0e0e0;
                           gridline-color:#333; border:1px solid #333; }
            QHeaderView::section { background:#252540; color:#aaa;
                                   font-size:11px; padding:5px; }
        """)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        left.addWidget(self.cart_table)

        # Remove row
        remove_btn = QPushButton("❌  Remove Selected")
        remove_btn.setStyleSheet(self._btn_style("#F44336"))
        remove_btn.clicked.connect(self._remove_selected)
        left.addWidget(remove_btn)

        root.addLayout(left, 3)

        # RIGHT — Summary & Payment
        right = QVBoxLayout()
        right.setSpacing(10)

        panel = QFrame()
        panel.setStyleSheet("""
            QFrame { background:#1a1a2e; border:1px solid #333;
                     border-radius:10px; padding:12px; }
        """)
        panel_layout = QVBoxLayout(panel)

        # Customer
        panel_layout.addWidget(QLabel("👤  Customer"))
        self.customer_box = QLineEdit()
        self.customer_box.setPlaceholderText("Walk-in Customer")
        self.customer_box.setStyleSheet(self._input_style())
        panel_layout.addWidget(self.customer_box)

        # GST type
        panel_layout.addWidget(QLabel("GST Type"))
        self.gst_type = QComboBox()
        self.gst_type.addItems(["CGST+SGST", "IGST", "Exempt"])
        self.gst_type.setStyleSheet(self._combo_style())
        self.gst_type.currentIndexChanged.connect(self._update_totals)
        panel_layout.addWidget(self.gst_type)

        # Discount
        panel_layout.addWidget(QLabel("Discount (%)"))
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setSuffix(" %")
        self.discount_spin.setStyleSheet(self._input_style())
        self.discount_spin.valueChanged.connect(self._update_totals)
        panel_layout.addWidget(self.discount_spin)

        # Totals
        self.subtotal_lbl  = self._summary_row(panel_layout, "Subtotal")
        self.gst_lbl       = self._summary_row(panel_layout, "GST")
        self.discount_lbl  = self._summary_row(panel_layout, "Discount")
        self.total_lbl     = self._summary_row(panel_layout, "TOTAL", big=True)

        # Payment mode
        panel_layout.addWidget(QLabel("Payment Mode"))
        self.payment_mode = QComboBox()
        self.payment_mode.addItems(["Cash", "UPI", "Card", "Bank Transfer", "Credit"])
        self.payment_mode.setStyleSheet(self._combo_style())
        panel_layout.addWidget(self.payment_mode)

        # UPI ref
        self.ref_box = QLineEdit()
        self.ref_box.setPlaceholderText("Reference / Transaction ID")
        self.ref_box.setStyleSheet(self._input_style())
        panel_layout.addWidget(self.ref_box)

        # Action buttons
        save_btn = QPushButton("💾  Save Draft")
        save_btn.setStyleSheet(self._btn_style("#607D8B"))
        save_btn.clicked.connect(self._save_draft)
        panel_layout.addWidget(save_btn)

        print_btn = QPushButton("🖨️  Print Invoice")
        print_btn.setStyleSheet(self._btn_style("#FF9800"))
        print_btn.clicked.connect(self._print_invoice)
        panel_layout.addWidget(print_btn)

        submit_btn = QPushButton("✅  GENERATE BILL")
        submit_btn.setStyleSheet(self._btn_style("#4CAF50", big=True))
        submit_btn.clicked.connect(self._generate_bill)
        panel_layout.addWidget(submit_btn)

        right.addWidget(panel)
        right.addStretch()
        root.addLayout(right, 1)

    # ── Helpers ──────────────────────────────────────────────
    def _summary_row(self, layout, label, big=False):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{'#fff' if big else '#aaa'}; font-size:{'14px' if big else '12px'}; font-weight:{'bold' if big else 'normal'};")
        val = QLabel("₹ 0.00")
        val.setStyleSheet(f"color:{'#4CAF50' if big else '#e0e0e0'}; font-size:{'15px' if big else '12px'}; font-weight:{'bold' if big else 'normal'};")
        val.setAlignment(Qt.AlignRight)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(val)
        layout.addLayout(row)
        return val

    def _input_style(self):
        return "background:#252540; color:#e0e0e0; border:1px solid #444; border-radius:5px; padding:6px;"

    def _combo_style(self):
        return "background:#252540; color:#e0e0e0; border:1px solid #444; border-radius:5px; padding:4px;"

    def _btn_style(self, color, big=False):
        sz = "13px" if big else "12px"
        pad = "10px 16px" if big else "8px 14px"
        return f"""
            QPushButton {{
                background:{color}22; color:{color};
                border:1px solid {color}; border-radius:6px;
                padding:{pad}; font-size:{sz}; font-weight:{'bold' if big else 'normal'};
            }}
            QPushButton:hover {{ background:{color}44; }}
        """

    # ── Logic ────────────────────────────────────────────────
    def _add_by_search(self):
        query = self.search_box.text().strip()
        if not query:
            return
        products = self.inv_mgr.search_products(query)
        if not products:
            QMessageBox.warning(self, "Not Found", f"No product found: {query}")
            return
        p = products[0]
        # Check if already in cart
        for item in self.cart:
            if item["product_id"] == p["id"]:
                item["qty"] += 1
                self._refresh_cart_table()
                self._update_totals()
                self.search_box.clear()
                return
        self.cart.append({
            "product_id": p["id"],
            "name":       p["name"],
            "hsn":        p.get("hsn_code", ""),
            "qty":        1,
            "rate":       p.get("selling_price", 0.0),
            "gst_pct":    p.get("gst_percent", 18.0),
        })
        self._refresh_cart_table()
        self._update_totals()
        self.search_box.clear()

    def _refresh_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            total = item["qty"] * item["rate"]
            self.cart_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item.get("hsn", ""))))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(item["qty"])))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"₹{item['rate']:.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{item['gst_pct']}%"))
            self.cart_table.setItem(row, 5, QTableWidgetItem(f"₹{total:.2f}"))

    def _update_totals(self):
        subtotal = sum(i["qty"] * i["rate"] for i in self.cart)
        disc_pct  = self.discount_spin.value()
        disc_amt  = subtotal * disc_pct / 100
        after_disc = subtotal - disc_amt
        # Average GST
        avg_gst = 0
        if self.cart:
            avg_gst = sum(i["gst_pct"] for i in self.cart) / len(self.cart)
        gst_amt = after_disc * avg_gst / 100
        total = after_disc + gst_amt
        self.subtotal_lbl.setText(f"₹ {subtotal:,.2f}")
        self.gst_lbl.setText(f"₹ {gst_amt:,.2f}")
        self.discount_lbl.setText(f"₹ {disc_amt:,.2f}")
        self.total_lbl.setText(f"₹ {total:,.2f}")

    def _remove_selected(self):
        rows = set(i.row() for i in self.cart_table.selectedIndexes())
        for r in sorted(rows, reverse=True):
            self.cart.pop(r)
        self._refresh_cart_table()
        self._update_totals()

    def _compute_totals(self) -> dict:
        subtotal = sum(i["qty"] * i["rate"] for i in self.cart)
        disc_pct  = self.discount_spin.value()
        disc_amt  = subtotal * disc_pct / 100
        after_disc = subtotal - disc_amt
        avg_gst = sum(i["gst_pct"] for i in self.cart) / max(len(self.cart), 1)
        gst_amt = after_disc * avg_gst / 100
        return {
            "subtotal":   subtotal,
            "discount":   disc_amt,
            "gst":        gst_amt,
            "total":      after_disc + gst_amt,
            "gst_type":   self.gst_type.currentText()
        }

    def _generate_bill(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Add products to cart first.")
            return
        t = self._compute_totals()
        mode = self.payment_mode.currentText().lower().replace(" ", "_")
        result = self.invoice_mgr.create_invoice(
            customer_name=self.customer_box.text() or "Walk-in Customer",
            items=self.cart,
            subtotal=t["subtotal"],
            discount=t["discount"],
            gst_amount=t["gst"],
            total=t["total"],
            gst_type=t["gst_type"],
            payment_mode=mode,
            created_by=self.user.get("uid", "")
        )
        if result.get("success"):
            inv_id = result["invoice_id"]
            self.pay_handler.record_payment(
                invoice_id=inv_id,
                amount=t["total"],
                mode=mode,
                reference=self.ref_box.text()
            )
            QMessageBox.information(self, "Success",
                f"✅ Invoice #{inv_id} created!\nTotal: ₹{t['total']:,.2f}")
            self.cart.clear()
            self._refresh_cart_table()
            self._update_totals()
        else:
            QMessageBox.critical(self, "Error", result.get("error", "Unknown error"))

    def _save_draft(self):
        QMessageBox.information(self, "Draft", "Draft saved (feature: save to local DB as draft).")

    def _print_invoice(self):
        if not self.cart:
            return
        t = self._compute_totals()
        try:
            self.printer.print_bill(
                customer=self.customer_box.text() or "Walk-in",
                items=self.cart,
                total=t["total"],
                gst=t["gst"]
            )
        except Exception as e:
            QMessageBox.warning(self, "Printer Error", str(e))
