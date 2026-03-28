import streamlit as st
from fpdf import FPDF
import database as db
from datetime import date

class PDF(FPDF):
    def header(self):
        # Intentamos usar Arial, si falla por encoding usamos helvetica
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'REPORTE GENERAL DEL HUERTO', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def mostrar_reportes(u_id):
    st.title("📄 Reportes PDF")
    st.write("Genera un documento con el estado actual de la bodega, terrenos y finanzas.")
    
    if st.button("🚀 Generar y Preparar Descarga"):
        try:
            pdf = PDF()
            pdf.add_page()
            
            # --- SECCIÓN BODEGA ---
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, "1. EXISTENCIAS EN BODEGA", ln=1)
            pdf.set_font("helvetica", size=10)
            exist = db.obtener_existencias()
            if not exist:
                pdf.cell(0, 8, "No hay existencias registradas.", ln=1)
            for n, u, s in exist:
                # Usamos encode('latin-1', 'replace') internamente para evitar caracteres raros
                linea = f"- {n}: {s:g} {u}"
                pdf.cell(0, 8, linea.encode('latin-1', 'replace').decode('latin-1'), ln=1)
            pdf.ln(5)
            
            # --- SECCIÓN FINANZAS ---
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, "2. RESUMEN FINANCIERO", ln=1)
            pdf.set_font("helvetica", size=10)
            t_c, t_o, t_v = db.calcular_resumen_financiero()
            pdf.cell(0, 8, f"Ingresos Totales: ${t_v:,.2f}", ln=1)
            pdf.cell(0, 8, f"Gastos Totales: ${t_c + t_o:,.2f}", ln=1)
            pdf.cell(0, 8, f"Balance: ${t_v - (t_c + t_o):,.2f}", ln=1)
            pdf.ln(5)

            # --- SECCIÓN TERRENOS ---
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, "3. LOTES / TERRENOS", ln=1)
            pdf.set_font("helvetica", size=10)
            lotes = db.obtener_terrenos()
            if not lotes:
                pdf.cell(0, 8, "No hay terrenos registrados.", ln=1)
            for l in lotes:
                linea_t = f"- {l[1]} ({l[2]}): {l[3]} arboles"
                pdf.cell(0, 8, linea_t.encode('latin-1', 'replace').decode('latin-1'), ln=1)

            # --- SOLUCIÓN AL ERROR ---
            # 1. Obtenemos el bytearray
            pdf_output = pdf.output() 
            # 2. Convertimos FORZOSAMENTE a bytes para Streamlit
            pdf_bytes = bytes(pdf_output) 
            
            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"Reporte_Huerto_{date.today()}.pdf",
                mime="application/pdf"
            )
            st.success("✅ El reporte está listo. Haz clic en el botón de arriba para guardarlo.")
            
        except Exception as e:
            st.error(f"Error al generar el PDF: {e}")
