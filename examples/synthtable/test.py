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


html = '<table><thead><tr><td></td><td colspan="2">WTP for baseline<span id="text_3b7f29c9-c435-4cfb-ba79-eb193d949ce0"> BH</span>I</td><td colspan="2"><b>WTP for BHI without ceiling</b></td><td colspan="2"><b>WTP for BHI without deductible</b></td><td colspan="2"><span id="text_2193d560-f783-4d5b-a3a5-859deb636200">WTP</span>  for  <span id="text_4b840bce-fb82-4360-abaf-b36656d3bccf">BHI</span>  <span id="text_d605597a-2879-45fa-b1e7-2d8704a5d706">without</span>  coinsurance </td></tr></thead><tbody><tr><td></td><td>Mean</td><td><span id="text_4b2f6268-c40a-4f89-8538-79fd656edfc0">95% CI</span></td><td>Mean</td><td>95% CI</td><td>Mean</td><td>95% CI</td><td><span id="text_3ab325b0-b868-48db-b7d4-25b6c91b0193">Mean</span> </td><td>95% CI</td></tr><tr><td>Non-equity weighted</td><td>30</td><td>27–33</td><td>51</td><td>46–56</td><td>43</td><td>37–49</td><td>47</td><td>40–54</td></tr><tr><td>Equity weighted</td><td></td><td></td><td></td><td><span id="text_715045df-d76f-4689-9385-4cbc9c6412b9"></span></td><td></td><td><span id="text_14ee33e5-08e1-4770-8530-a51533c15cb7"></span></td><td></td><td></td></tr><tr><td><i>e </i>= 1.0</td><td>38</td><td>32–43</td><td>66</td><td>55–76</td><td>56</td><td>46–65</td><td><span id="text_bfe6f9c8-3f52-4e3d-bc74-a9f545ab7e83">59</span> </td><td>48–70</td></tr><tr><td><i>e </i>= 1.5</td><td>67</td><td>47–<span id="text_01a83dff-d205-48af-9de4-2a2e512f3b19">86</span></td><td>121</td><td>83–159</td><td><span id="text_9d08375d-7f50-4c92-9e58-851e281d158b">102</span> </td><td>70–134</td><td><span id="text_b1f0c7bd-b1de-41ce-8f6f-02156312f8f7">107</span> </td><td>69–145</td></tr><tr><td><i>e </i>= 2.0</td><td><span id="text_ed65a8e9-435a-47a9-8d94-c92a8ea68d00">166</span> </td><td>93–239</td><td>310</td><td><span id="text_678829de-9f04-459d-bf6c-b65b10c13ac2">170–450</span> </td><td>263</td><td>145–382</td><td><span id="text_8701b7bb-e2a5-4ab6-af63-af8a7ba48486">275</span> </td><td>133–417</td></tr></tbody></table>'
set_inner_border_col("tbody", html)
