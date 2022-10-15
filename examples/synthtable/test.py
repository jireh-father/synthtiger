import numpy as np
from bs4 import BeautifulSoup


def set_inner_border_col(css_selector, html, nums_row=9, nums_col=9):
    bs = BeautifulSoup(html, 'html.parser')
    tr_tags = bs.find(css_selector).find_all("tr")
    table_row_span_map = np.full((nums_row, nums_col), False)

    for ridx, tr_element in enumerate(tr_tags):
        real_cidx = 0
        td_tags = tr_element.find_all("td")
        for cidx, td_tag in enumerate(td_tags):
            while table_row_span_map[ridx][real_cidx]:
                real_cidx += 1

            has_row_span = td_tag.has_attr('rowspan')
            has_col_span = td_tag.has_attr('colspan')
            if has_row_span and has_col_span:
                table_row_span_map[ridx:ridx + int(td_tag['rowspan']),
                real_cidx:real_cidx + int(td_tag['colspan'])] = True
            elif has_row_span:
                table_row_span_map[ridx:ridx + int(td_tag['rowspan']), real_cidx] = True
            elif has_col_span:
                table_row_span_map[ridx, real_cidx:real_cidx + int(td_tag['colspan'])] = True

            real_cidx += int(td_tag['colspan']) if has_col_span else 1

            # last tag
            if cidx == len(td_tags) - 1:
                if real_cidx < nums_col and all([table_row_span_map[ridx][inner_cidx] for inner_cidx in
                                                 range(real_cidx, nums_col)]):
                    print("all span")
                    print('{} tr:nth-child({}) td:nth-child({})'.format(css_selector, ridx + 1, cidx + 1))
                else:
                    print(table_row_span_map)
                    print("no", '{} tr:nth-child({}) td:nth-child({})'.format(css_selector, ridx + 1, cidx + 1))
            else:
                print('{} tr:nth-child({}) td:nth-child({})'.format(css_selector, ridx + 1, cidx + 1))


html = '<table><thead><tr><td></td><td colspan="4"><b>Bladder cancer</b></td><td colspan="4"><b>Prostate cancer</b></td></tr><tr><td rowspan="2"></td><td rowspan="2"><span id="text_c34035eb-6f8e-462d-b964-46682e041af2">beta</span> </td><td colspan="2"><b>95% CI</b></td><td rowspan="2"><span id="text_521e0e1a-6c93-425d-aeea-0ea9e2bd43e8">p-value</span> </td><td rowspan="2">b<span id="text_f292b6a0-587f-4c7a-ad4c-d64ece3572fa">et</span>a</td><td colspan="2">95%<span id="text_69574327-58af-48f3-ac78-6c04c500c4f6"> CI</span></td><td rowspan="2"><b><i>p</i>-value</b></td></tr><tr><td><b>Lower</b></td><td><b>Upper</b></td><td><b>Lower</b></td><td><span id="text_94df9b7c-b04c-465a-aec2-64ebede34874">Upper</span> </td></tr></thead><tbody><tr><td>Area (non-metropolitan)</td><td>1.401</td><td>0.558</td><td><span id="text_ece966c3-c8db-4d5d-94af-b5e393a0d1a0">2.243</span> </td><td>0.001</td><td></td><td></td><td></td><td></td></tr><tr><td>No. of training hospital</td><td></td><td></td><td></td><td></td><td>1.487</td><td>0.460</td><td>2.514</td><td>0.005</td></tr><tr><td>D<span id="text_e8bb072b-2d02-46e3-9a13-5e526f116f01">octor d</span>ensity</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td><span id="text_0fa2ff72-25b0-4040-ae59-1955e6e55e95"></span></td></tr><tr><td>Urologist density</td><td>0.384</td><td>–0.216</td><td>0.985</td><td>0.206</td><td></td><td></td><td><span id="text_019117fe-eaf3-4edd-baf6-23b86c48a096"></span> </td><td></td></tr><tr><td><span id="text_565ff7f0-a2d3-44d1-b371-a93fd048a763">Inco</span>me</td><td>0.000</td><td>0.000</td><td>0.000</td><td>0.055</td><td></td><td><span id="text_c0f95242-60ce-49f1-8526-6217ab9f4e8c"></span> </td><td></td><td></td></tr><tr><td>Te<span id="text_f2e3a53e-e65c-4907-8cf4-5f3bb1f10a91">mp</span></td><td></td><td></td><td></td><td><span id="text_183171b9-396f-4f5e-8053-86d3ede9488c"></span></td><td>–3.677</td><td>–9.865</td><td>2.512</td><td>0.240</td></tr></tbody></table>'
set_inner_border_col("thead", html)
