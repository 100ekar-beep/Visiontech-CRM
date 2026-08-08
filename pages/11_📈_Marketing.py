        class PDF(FPDF):
            def header(self):
                self.set_fill_color(30, 27, 75)
                self.rect(10, 10, 190, 24, 'F')

                self.set_font('DejaVu', 'B', 14)
                self.set_text_color(56, 189, 248)
                self.set_xy(10, 13)
                self.cell(190, 8, 'WHATSAPP MARKETING CAMPAIGN REPORT', 0, 1, 'C')

                self.set_font('DejaVu', '', 9)
                self.set_text_color(226, 232, 240)
                self.set_xy(10, 22)
                self.cell(
                    190,
                    6,
                    f'Target List: {rep["list_name"]}  |  Template: {rep["template"]}  |  Date & Time: {rep.get("timestamp", "N/A")}',
                    0,
                    1,
                    'C'
                )
                self.ln(12)

            def footer(self):
                self.set_y(-15)
                self.set_font('DejaVu', 'I', 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


        def generate_pdf():
            pdf = PDF()

            # ==========================================================
            # HINDI / DEVANAGARI UNICODE FONT FIX
            # ==========================================================
            # Streamlit Cloud par font installed na ho to automatically
            # Noto Sans Devanagari download hoga.
            #
            # IMPORTANT:
            # Hindi text ko English/Roman phonetic mein convert nahi kiya
            # ja raha hai. Original Hindi text PDF mein hi jayega.
            # ==========================================================

            import glob

            font_dir = "/tmp/whatsapp_pdf_fonts"
            os.makedirs(font_dir, exist_ok=True)

            devanagari_font = os.path.join(
                font_dir,
                "NotoSansDevanagari-Regular.ttf"
            )

            latin_font = None

            # ----------------------------------------------------------
            # 1. Check if Devanagari font already exists
            # ----------------------------------------------------------
            devanagari_candidates = [
                "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
            ]

            for font_path in devanagari_candidates:
                if os.path.exists(font_path):
                    devanagari_font = font_path
                    break

            # ----------------------------------------------------------
            # 2. Search system folders
            # ----------------------------------------------------------
            if not os.path.exists(devanagari_font):
                discovered_fonts = glob.glob(
                    "/usr/share/fonts/**/*NotoSansDevanagari-Regular.ttf",
                    recursive=True
                )

                if discovered_fonts:
                    devanagari_font = discovered_fonts[0]

            # ----------------------------------------------------------
            # 3. Download Noto Sans Devanagari if not available
            # ----------------------------------------------------------
            if not os.path.exists(devanagari_font):

                font_url = (
                    "https://github.com/openmaptiles/fonts/raw/master/"
                    "noto-sans/NotoSansDevanagari-Regular.ttf"
                )

                try:
                    font_response = requests.get(
                        font_url,
                        timeout=30
                    )

                    font_response.raise_for_status()

                    with open(devanagari_font, "wb") as font_file:
                        font_file.write(font_response.content)

                except Exception as e:
                    raise RuntimeError(
                        "Hindi font download nahi ho paya. "
                        f"Font Error: {str(e)}"
                    )

            # ----------------------------------------------------------
            # 4. Find normal Latin font
            # ----------------------------------------------------------
            latin_candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/opentype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ]

            for font_path in latin_candidates:
                if os.path.exists(font_path):
                    latin_font = font_path
                    break

            if latin_font is None:
                discovered_latin = glob.glob(
                    "/usr/share/fonts/**/*DejaVuSans.ttf",
                    recursive=True
                )

                if discovered_latin:
                    latin_font = discovered_latin[0]

            # ----------------------------------------------------------
            # 5. If DejaVu not available, use Noto Devanagari for all
            # ----------------------------------------------------------
            if latin_font is None:
                latin_font = devanagari_font

            # ----------------------------------------------------------
            # 6. Register fonts
            # ----------------------------------------------------------
            pdf.add_font(
                'DejaVu',
                '',
                latin_font
            )

            pdf.add_font(
                'DejaVu',
                'B',
                latin_font
            )

            pdf.add_font(
                'DejaVu',
                'I',
                latin_font
            )

            pdf.add_font(
                'DejaVu',
                'BI',
                latin_font
            )

            pdf.add_font(
                'NotoDev',
                '',
                devanagari_font
            )

            # ----------------------------------------------------------
            # 7. Hindi fallback font
            # ----------------------------------------------------------
            # fpdf2 automatically uses NotoDev for Devanagari characters.
            # ----------------------------------------------------------
            pdf.set_fallback_fonts(
                ['NotoDev']
            )

            pdf.add_page()

            pdf.set_auto_page_break(
                auto=True,
                margin=15
            )

            # ==========================================================
            # CAMPAIGN SUMMARY METRICS
            # ==========================================================

            pdf.set_font(
                'DejaVu',
                'B',
                12
            )

            pdf.set_text_color(
                30,
                41,
                59
            )

            pdf.cell(
                190,
                8,
                'CAMPAIGN SUMMARY METRICS:',
                0,
                1,
                'C'
            )

            pdf.ln(2)

            box_width = 58
            box_height = 20
            start_x = 10
            y_pos = pdf.get_y()

            # ----------------------------------------------------------
            # Box 1 - Total
            # ----------------------------------------------------------

            pdf.set_fill_color(
                254,
                243,
                199
            )

            pdf.set_draw_color(
                217,
                119,
                6
            )

            pdf.set_line_width(0.6)

            pdf.rect(
                start_x,
                y_pos,
                box_width,
                box_height,
                'DF'
            )

            pdf.set_xy(
                start_x,
                y_pos + 3
            )

            pdf.set_font(
                'DejaVu',
                'B',
                9
            )

            pdf.set_text_color(
                180,
                83,
                9
            )

            pdf.cell(
                box_width,
                5,
                'Total Target Numbers',
                0,
                1,
                'C'
            )

            pdf.set_xy(
                start_x,
                y_pos + 10
            )

            pdf.set_font(
                'DejaVu',
                'B',
                12
            )

            pdf.set_text_color(
                146,
                64,
                14
            )

            pdf.cell(
                box_width,
                6,
                str(rep['total']),
                0,
                0,
                'C'
            )

            # ----------------------------------------------------------
            # Box 2 - Success
            # ----------------------------------------------------------

            start_x += box_width + 8

            pdf.set_fill_color(
                220,
                252,
                231
            )

            pdf.set_draw_color(
                22,
                163,
                74
            )

            pdf.rect(
                start_x,
                y_pos,
                box_width,
                box_height,
                'DF'
            )

            pdf.set_xy(
                start_x,
                y_pos + 3
            )

            pdf.set_font(
                'DejaVu',
                'B',
                9
            )

            pdf.set_text_color(
                21,
                128,
                61
            )

            pdf.cell(
                box_width,
                5,
                'Successfully Sent',
                0,
                1,
                'C'
            )

            pdf.set_xy(
                start_x,
                y_pos + 10
            )

            pdf.set_font(
                'DejaVu',
                'B',
                12
            )

            pdf.set_text_color(
                20,
                83,
                45
            )

            pdf.cell(
                box_width,
                6,
                str(rep['success']),
                0,
                0,
                'C'
            )

            # ----------------------------------------------------------
            # Box 3 - Failed
            # ----------------------------------------------------------

            start_x += box_width + 8

            pdf.set_fill_color(
                254,
                215,
                170
            )

            pdf.set_draw_color(
                234,
                88,
                12
            )

            pdf.rect(
                start_x,
                y_pos,
                box_width,
                box_height,
                'DF'
            )

            pdf.set_xy(
                start_x,
                y_pos + 3
            )

            pdf.set_font(
                'DejaVu',
                'B',
                9
            )

            pdf.set_text_color(
                194,
                65,
                12
            )

            pdf.cell(
                box_width,
                5,
                'Failed',
                0,
                1,
                'C'
            )

            pdf.set_xy(
                start_x,
                y_pos + 10
            )

            pdf.set_font(
                'DejaVu',
                'B',
                12
            )

            pdf.set_text_color(
                154,
                52,
                18
            )

            pdf.cell(
                box_width,
                6,
                str(rep['failed']),
                0,
                0,
                'C'
            )

            pdf.set_y(
                y_pos + box_height + 10
            )

            # ==========================================================
            # MESSAGE PREVIEW
            # ==========================================================

            pdf.set_font(
                'DejaVu',
                'B',
                11
            )

            pdf.set_text_color(
                30,
                41,
                59
            )

            pdf.cell(
                0,
                8,
                'MESSAGE SENT PREVIEW:',
                0,
                1,
                'L'
            )

            pdf.set_fill_color(
                255,
                255,
                255
            )

            pdf.set_draw_color(
                203,
                213,
                225
            )

            pdf.set_line_width(0.4)

            # ----------------------------------------------------------
            # VERY IMPORTANT
            # ----------------------------------------------------------
            # Original Hindi message directly use karna hai.
            #
            # Koi Hindi-to-English mapping nahi.
            # Koi transliteration nahi.
            # Koi latin-1 encode/decode nahi.
            # ----------------------------------------------------------

            raw_msg = rep['message']

            pdf.set_font(
                'DejaVu',
                '',
                9
            )

            pdf.set_text_color(
                51,
                65,
                85
            )

            pdf.multi_cell(
                190,
                5,
                raw_msg,
                border=1,
                fill=True
            )

            pdf.ln(8)

            # ==========================================================
            # DETAILED CONTACT DELIVERY STATUS
            # ==========================================================

            pdf.set_font(
                'DejaVu',
                'B',
                11
            )

            pdf.set_text_color(
                30,
                41,
                59
            )

            pdf.cell(
                0,
                8,
                'DETAILED CONTACT DELIVERY STATUS:',
                0,
                1,
                'L'
            )

            # ----------------------------------------------------------
            # Table Header
            # ----------------------------------------------------------

            pdf.set_fill_color(
                30,
                27,
                75
            )

            pdf.set_text_color(
                255,
                255,
                255
            )

            pdf.set_font(
                'DejaVu',
                'B',
                9
            )

            pdf.cell(
                15,
                7,
                'Sr',
                1,
                0,
                'C',
                fill=True
            )

            pdf.cell(
                65,
                7,
                'Contact Name',
                1,
                0,
                'C',
                fill=True
            )

            pdf.cell(
                45,
                7,
                'Mobile Number',
                1,
                0,
                'C',
                fill=True
            )

            pdf.cell(
                65,
                7,
                'Delivery Status',
                1,
                1,
                'C',
                fill=True
            )

            # ----------------------------------------------------------
            # Table Rows
            # ----------------------------------------------------------

            pdf.set_font(
                'DejaVu',
                '',
                9
            )

            for idx, item in enumerate(
                rep["logs"],
                1
            ):

                # Original contact name — NO transliteration
                clean_name = item["Name"]

                # Original status
                safe_status = item["Status"]

                if idx % 2 == 0:

                    pdf.set_fill_color(
                        241,
                        245,
                        249
                    )

                else:

                    pdf.set_fill_color(
                        255,
                        255,
                        255
                    )

                pdf.set_text_color(
                    51,
                    65,
                    85
                )

                pdf.cell(
                    15,
                    6,
                    str(idx),
                    1,
                    0,
                    'C',
                    fill=True
                )

                pdf.cell(
                    65,
                    6,
                    clean_name,
                    1,
                    0,
                    'L',
                    fill=True
                )

                pdf.cell(
                    45,
                    6,
                    str(item["Mobile"]),
                    1,
                    0,
                    'C',
                    fill=True
                )

                pdf.cell(
                    65,
                    6,
                    safe_status,
                    1,
                    1,
                    'L',
                    fill=True
                )

            # ----------------------------------------------------------
            # Return PDF bytes
            # ----------------------------------------------------------

            return bytes(
                pdf.output(dest='S')
            )


        pdf_bytes = generate_pdf()
