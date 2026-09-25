"""UBL-TR (Universal Business Language) XML Transformation and Serialization Service.

Converts relational database invoice models into Gelir İdaresi Başkanlığı (GİB)
compliant UBL 2.1 / UBL-TR 1.2 XML documents using Python's xml.etree.ElementTree.
"""
from datetime import date
from decimal import Decimal
import re
from typing import Dict, Any, Optional
import uuid
import xml.etree.ElementTree as ET
from fastapi import HTTPException, status
from app.models.invoice_header import InvoiceHeader


class UBLTRService:
    """Service class providing serialization, validation, and XML tree construction for UBL-TR."""

    # Standard XML Namespaces for UBL-TR 1.2
    NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

    def __init__(self):
        # Register standard namespaces so ElementTree uses prefixes (cac, cbc) instead of ns0, ns1
        ET.register_namespace("", self.NS_INVOICE)
        ET.register_namespace("cac", self.NS_CAC)
        ET.register_namespace("cbc", self.NS_CBC)
        ET.register_namespace("xsi", self.NS_XSI)

    @staticmethod
    def validate_vkn_tckn(identifier: str) -> bool:
        """
        Validate Turkish Tax Identification Number (VKN: 10 digits)
        or Turkish Citizen Identification Number (TCKN: 11 digits).
        """
        if not identifier:
            return False
        clean_id = identifier.strip()
        # Must be 10 digits (VKN) or 11 digits (TCKN)
        return bool(re.fullmatch(r"\d{10}|\d{11}", clean_id))

    def _tag(self, ns: str, name: str) -> str:
        """Helper to build namespaced element tag string."""
        return f"{{{ns}}}{name}"

    def build_xml_tree(
        self,
        invoice: InvoiceHeader,
        supplier_info: Optional[Dict[str, Any]] = None
    ) -> ET.Element:
        """
        Constructs a complete UBL-TR XML ElementTree for a given InvoiceHeader.
        Validates mandatory fields (VKN/TCKN, customer name, lines).
        """
        customer = invoice.customer
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fatura müşteri bilgisi eksik. UBL-TR XML oluşturulamaz."
            )

        # 1. Mandatory VKN/TCKN validation
        cust_tax_num = customer.tax_number.strip() if customer.tax_number else ""
        if not self.validate_vkn_tckn(cust_tax_num):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Geçersiz müşteri vergi kimlik numarası ('{cust_tax_num}'). VKN 10 haneli, TCKN 11 haneli olmalıdır."
            )

        if not invoice.lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fatura kalemi bulunmayan faturanın UBL-TR belgesi oluşturulamaz."
            )

        # Supplier default config
        supplier = supplier_info or {
            "vkn": "1234567890",
            "name": "ERP E-Dönüşüm ve Bilişim Hizmetleri A.Ş.",
            "city": "İstanbul",
            "district": "Sarıyer",
            "street": "Büyükdere Cad. No:199",
            "email": "muhasebe@erpentegrasyon.com",
            "phone": "+90 212 555 0000"
        }

        # 2. Document Root
        root = ET.Element(self._tag(self.NS_INVOICE, "Invoice"))

        # 3. Document Headers (Common Basic Components)
        ubl_version = ET.SubElement(root, self._tag(self.NS_CBC, "UBLVersionID"))
        ubl_version.text = "2.1"

        customization_id = ET.SubElement(root, self._tag(self.NS_CBC, "CustomizationID"))
        customization_id.text = "TR1.2"

        profile_id = ET.SubElement(root, self._tag(self.NS_CBC, "ProfileID"))
        profile_id.text = "TICARIFATURA"

        inv_id = ET.SubElement(root, self._tag(self.NS_CBC, "ID"))
        inv_id.text = invoice.invoice_number

        copy_indicator = ET.SubElement(root, self._tag(self.NS_CBC, "CopyIndicator"))
        copy_indicator.text = "false"

        inv_uuid = ET.SubElement(root, self._tag(self.NS_CBC, "UUID"))
        inv_uuid.text = invoice.uuid or str(uuid.uuid4())

        issue_date = ET.SubElement(root, self._tag(self.NS_CBC, "IssueDate"))
        issue_date.text = invoice.invoice_date.strftime("%Y-%m-%d") if isinstance(invoice.invoice_date, (date,)) else str(invoice.invoice_date)

        inv_type = ET.SubElement(root, self._tag(self.NS_CBC, "InvoiceTypeCode"))
        inv_type.text = "SATIS"

        currency = ET.SubElement(root, self._tag(self.NS_CBC, "DocumentCurrencyCode"))
        currency.text = "TRY"

        line_count = ET.SubElement(root, self._tag(self.NS_CBC, "LineCountNumeric"))
        line_count.text = str(len(invoice.lines))

        # 4. AccountingSupplierParty (Satıcı Bilgileri)
        supplier_party = ET.SubElement(root, self._tag(self.NS_CAC, "AccountingSupplierParty"))
        s_party = ET.SubElement(supplier_party, self._tag(self.NS_CAC, "Party"))

        s_party_id = ET.SubElement(s_party, self._tag(self.NS_CAC, "PartyIdentification"))
        s_id = ET.SubElement(s_party_id, self._tag(self.NS_CBC, "ID"), attrib={"schemeID": "VKN"})
        s_id.text = supplier["vkn"]

        s_party_name = ET.SubElement(s_party, self._tag(self.NS_CAC, "PartyName"))
        s_name = ET.SubElement(s_party_name, self._tag(self.NS_CBC, "Name"))
        s_name.text = supplier["name"]

        s_address = ET.SubElement(s_party, self._tag(self.NS_CAC, "PostalAddress"))
        s_street = ET.SubElement(s_address, self._tag(self.NS_CBC, "StreetName"))
        s_street.text = supplier["street"]
        s_district = ET.SubElement(s_address, self._tag(self.NS_CBC, "CitySubdivisionName"))
        s_district.text = supplier["district"]
        s_city = ET.SubElement(s_address, self._tag(self.NS_CBC, "CityName"))
        s_city.text = supplier["city"]

        # 5. AccountingCustomerParty (Alıcı Bilgileri)
        customer_party = ET.SubElement(root, self._tag(self.NS_CAC, "AccountingCustomerParty"))
        c_party = ET.SubElement(customer_party, self._tag(self.NS_CAC, "Party"))

        c_party_id = ET.SubElement(c_party, self._tag(self.NS_CAC, "PartyIdentification"))
        scheme = "TCKN" if len(cust_tax_num) == 11 else "VKN"
        c_id = ET.SubElement(c_party_id, self._tag(self.NS_CBC, "ID"), attrib={"schemeID": scheme})
        c_id.text = cust_tax_num

        c_party_name = ET.SubElement(c_party, self._tag(self.NS_CAC, "PartyName"))
        c_name = ET.SubElement(c_party_name, self._tag(self.NS_CBC, "Name"))
        c_name.text = customer.name

        c_address = ET.SubElement(c_party, self._tag(self.NS_CAC, "PostalAddress"))
        c_street = ET.SubElement(c_address, self._tag(self.NS_CBC, "StreetName"))
        c_street.text = customer.address or "Türkiye"

        if customer.email or customer.phone:
            c_contact = ET.SubElement(c_party, self._tag(self.NS_CAC, "Contact"))
            if customer.phone:
                c_tel = ET.SubElement(c_contact, self._tag(self.NS_CBC, "Telephone"))
                c_tel.text = customer.phone
            if customer.email:
                c_mail = ET.SubElement(c_contact, self._tag(self.NS_CBC, "ElectronicMail"))
                c_mail.text = customer.email

        # 6. TaxTotal (Genel Vergi Özeti)
        tax_total = ET.SubElement(root, self._tag(self.NS_CAC, "TaxTotal"))
        tax_amount = ET.SubElement(tax_total, self._tag(self.NS_CBC, "TaxAmount"), attrib={"currencyID": "TRY"})
        tax_amount.text = f"{Decimal(str(invoice.total_vat)):.2f}"

        tax_subtotal = ET.SubElement(tax_total, self._tag(self.NS_CAC, "TaxSubtotal"))
        taxable_amount = ET.SubElement(tax_subtotal, self._tag(self.NS_CBC, "TaxableAmount"), attrib={"currencyID": "TRY"})
        taxable_amount.text = f"{Decimal(str(invoice.total_amount)):.2f}"
        sub_tax_amount = ET.SubElement(tax_subtotal, self._tag(self.NS_CBC, "TaxAmount"), attrib={"currencyID": "TRY"})
        sub_tax_amount.text = f"{Decimal(str(invoice.total_vat)):.2f}"

        tax_category = ET.SubElement(tax_subtotal, self._tag(self.NS_CAC, "TaxCategory"))
        tax_scheme = ET.SubElement(tax_category, self._tag(self.NS_CAC, "TaxScheme"))
        scheme_name = ET.SubElement(tax_scheme, self._tag(self.NS_CBC, "Name"))
        scheme_name.text = "KDV"
        scheme_code = ET.SubElement(tax_scheme, self._tag(self.NS_CBC, "TaxTypeCode"))
        scheme_code.text = "0015"

        # 7. LegalMonetaryTotal (Genel Toplamlar)
        monetary_total = ET.SubElement(root, self._tag(self.NS_CAC, "LegalMonetaryTotal"))
        line_ext = ET.SubElement(monetary_total, self._tag(self.NS_CBC, "LineExtensionAmount"), attrib={"currencyID": "TRY"})
        line_ext.text = f"{Decimal(str(invoice.total_amount)):.2f}"
        tax_excl = ET.SubElement(monetary_total, self._tag(self.NS_CBC, "TaxExclusiveAmount"), attrib={"currencyID": "TRY"})
        tax_excl.text = f"{Decimal(str(invoice.total_amount)):.2f}"
        tax_incl = ET.SubElement(monetary_total, self._tag(self.NS_CBC, "TaxInclusiveAmount"), attrib={"currencyID": "TRY"})
        tax_incl.text = f"{Decimal(str(invoice.grand_total)):.2f}"
        payable = ET.SubElement(monetary_total, self._tag(self.NS_CBC, "PayableAmount"), attrib={"currencyID": "TRY"})
        payable.text = f"{Decimal(str(invoice.grand_total)):.2f}"

        # 8. InvoiceLines (Fatura Kalemleri)
        for idx, line in enumerate(invoice.lines, start=1):
            inv_line = ET.SubElement(root, self._tag(self.NS_CAC, "InvoiceLine"))
            l_id = ET.SubElement(inv_line, self._tag(self.NS_CBC, "ID"))
            l_id.text = str(idx)

            l_qty = ET.SubElement(inv_line, self._tag(self.NS_CBC, "InvoicedQuantity"), attrib={"unitCode": "NIU"})
            l_qty.text = f"{Decimal(str(line.quantity)):.2f}"

            l_amount = ET.SubElement(inv_line, self._tag(self.NS_CBC, "LineExtensionAmount"), attrib={"currencyID": "TRY"})
            l_amount.text = f"{Decimal(str(line.line_total)):.2f}"

            # Line Tax Total
            l_tax_total = ET.SubElement(inv_line, self._tag(self.NS_CAC, "TaxTotal"))
            l_tax_amt = ET.SubElement(l_tax_total, self._tag(self.NS_CBC, "TaxAmount"), attrib={"currencyID": "TRY"})
            l_tax_amt.text = f"{Decimal(str(line.vat_amount)):.2f}"

            l_tax_sub = ET.SubElement(l_tax_total, self._tag(self.NS_CAC, "TaxSubtotal"))
            l_taxable = ET.SubElement(l_tax_sub, self._tag(self.NS_CBC, "TaxableAmount"), attrib={"currencyID": "TRY"})
            l_taxable.text = f"{Decimal(str(line.line_total)):.2f}"
            l_sub_tax_amt = ET.SubElement(l_tax_sub, self._tag(self.NS_CBC, "TaxAmount"), attrib={"currencyID": "TRY"})
            l_sub_tax_amt.text = f"{Decimal(str(line.vat_amount)):.2f}"
            l_percent = ET.SubElement(l_tax_sub, self._tag(self.NS_CBC, "Percent"))
            l_percent.text = f"{Decimal(str(line.vat_rate)):.2f}"

            l_tax_cat = ET.SubElement(l_tax_sub, self._tag(self.NS_CAC, "TaxCategory"))
            l_scheme = ET.SubElement(l_tax_cat, self._tag(self.NS_CAC, "TaxScheme"))
            l_sch_name = ET.SubElement(l_scheme, self._tag(self.NS_CBC, "Name"))
            l_sch_name.text = "KDV"
            l_sch_code = ET.SubElement(l_scheme, self._tag(self.NS_CBC, "TaxTypeCode"))
            l_sch_code.text = "0015"

            # Line Item
            item = ET.SubElement(inv_line, self._tag(self.NS_CAC, "Item"))
            prod_name = line.product.name if line.product else "Hizmet/Ürün"
            prod_code = line.product.code if line.product else f"PRD-{line.product_id}"
            item_desc = ET.SubElement(item, self._tag(self.NS_CBC, "Description"))
            item_desc.text = prod_name
            item_name = ET.SubElement(item, self._tag(self.NS_CBC, "Name"))
            item_name.text = prod_code

            # Line Price
            price = ET.SubElement(inv_line, self._tag(self.NS_CAC, "Price"))
            price_amt = ET.SubElement(price, self._tag(self.NS_CBC, "PriceAmount"), attrib={"currencyID": "TRY"})
            price_amt.text = f"{Decimal(str(line.unit_price)):.2f}"

        return root

    def generate_ubl_xml(
        self,
        invoice: InvoiceHeader,
        supplier_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Builds and serializes the UBL-TR XML tree into an indented UTF-8 XML document string.
        """
        root = self.build_xml_tree(invoice=invoice, supplier_info=supplier_info)
        ET.indent(root, space="    ")
        raw_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return raw_xml.decode("utf-8")


ubl_service = UBLTRService()
