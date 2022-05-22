import datetime

UNHCR_MOCK_DATA_PAGE_1_RAW = '''
<!DOCTYPE html>
<html lang="en"
   dir='ltr'   >
   <body>
      <div class='pgSearch_layout'>
         <div class='pgSearch_layout_results'>
            <div class='pgSearch_layout_results_inner'>
               <div class='pgSearch_results'>
                  <ul class='searchResults'>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                           <h2 class='searchResultItem_title'>
                              <a href="https://data2.unhcr.org/en/documents/details/92127">
                              UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022
                              </a>
                           </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92127' data-title="UNHCR - Pakistan Ov 2022"
                                       title="Download"
                                       >
                                    <img src='https://data2.unhcr.org/bundles/common/img/icons/download-orange.svg' alt=''>
                                    Download
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92127"
                                       >
                                    View
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           <div class='searchResultItem_body'>
                              UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;19 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92127"
                                    href="https://data2.unhcr.org/en/documents/details/92127"
                                    data-visibility-toggle='#widget_6260e5417c608shareDialog_document_92127'>
                                 Share this page:test
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417c608shareDialog_document_92127'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417c608shareDialog_document_92127'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 20 2022" data-share data-url='https://data2.unhcr.org/en/documents/details/92127'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92127'
                                             data-title='UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92127'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                           <h2 class='searchResultItem_title'>
                              <a target="_blank" href="https://data2.unhcr.org/en/documents/details/92134">
                              UNHCR Mozambique IDP Response External Update _February 2022
                              </a>
                           </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92134' data-title="UNHCR Mozambique IDP Response External Update _February 2022"
                                       title="Download"
                                       >
                                    Download
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92134"
                                       target="_blank"
                                       title="View"
                                       >
                                    View
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           <div class='searchResultItem_body'>
                              UNHCR Mozambique IDP Response External Update _February 2022
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;17 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92134"
                                    href="https://data2.unhcr.org/en/documents/details/92134"
                                    data-visibility-toggle='#widget_6260e5417c940shareDialog_document_92134'>
                                 Share this page:
                                 <i class='share_link_icon'></i>
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417c940shareDialog_document_92134'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417c940shareDialog_document_92134'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="UNHCR Mozambique IDP Response External Update _February 2022" data-summary="UNHCR Moza 2022" data-share data-url='https://data2.unhcr.org/en/documents/details/92134'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92134'
                                             data-title='UNHCR Mozambique IDP Response External Update _February 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92134'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                            <h2 class='searchResultItem_title'>
                                <a target="_blank" href="https://data2.unhcr.org/en/documents/details/92134">
                                Factsheet ProNexus March 2022
                                </a>
                            </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92148' data-title="Factsheet ProNexus March 2022"
                                       title="Download"
                                       >
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92148"
                                       >
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;11 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92148"
                                    href="https://data2.unhcr.org/en/documents/details/92148"
                                    data-visibility-toggle='#widget_6260e5417cd7bshareDialog_document_92148'>
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417cd7bshareDialog_document_92148'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417cd7bshareDialog_document_92148'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="Factsheet ProNexus March 2022" data-summary="" data-share data-url='https://data2.unhcr.org/en/documents/details/92148'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92148'
                                             data-title='Factsheet ProNexus March 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92148'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                           <h2 class='searchResultItem_title'>
                              <a target="_blank" href="https://data2.unhcr.org/en/documents/details/92125">
                              Myanmar UNHCR displacement overview 18 Apr 2022
                              </a>
                           </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92125' data-title="Myanmar UNHCR displacement overview 18 Apr 2022"
                                       title="Download"
                                       >
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92125"
                                       >
                                    View
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           <div class='searchResultItem_body'>
                              Displacement Overview as of 18 Apr 2022
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;19 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92125"
                                    href="https://data2.unhcr.org/en/documents/details/92125"
                                    data-visibility-toggle='#widget_6260e5417d135shareDialog_document_92125'>
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417d135shareDialog_document_92125'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417d135shareDialog_document_92125'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="Myanmar UNHCR displacement overview 18 Apr 2022" data-summary="Displacement Overview as of 18 Apr 2022" data-share data-url='https://data2.unhcr.org/en/documents/details/92125'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92125'
                                             data-title='Myanmar UNHCR displacement overview 18 Apr 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92125'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                  </ul>
                    <div class='pgSearch_results_footer'>
                        <nav>
                        <ul class="pagination">
                            <li class="page-item">
                                <a class="page-link" rel="prev" href="/en/search?page=1">&laquo;&nbsp;Previous</a>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="/en/search?page=1">1</a>
                            </li>
                            <li class="page-item active">
                                <span class="page-link">2</span>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="/en/search?page=3">3</a>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="/en/search?page=4">4</a>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="/en/search?page=5">5</a>
                            </li>
                            <li class="page-item disabled">
                                <span class="page-link">&hellip;</span>
                            </li>
                            <li class="page-item">
                                <a class="page-link" href="/en/search?page=6936">6936</a>
                            </li>
                            <li class="page-item">
                                <a class="page-link" rel="next" href="/en/search?page=3">Next&nbsp;&raquo;</a>
                            </li>
                        </ul>
                        </nav>
                    </div>
                 </div>
               </div>
            </div>
         </div>
      </div>
   </body>
</html>
'''

UNHCR_MOCK_DATA_PAGE_2_RAW = '''
<!DOCTYPE html>
<html lang="en"
   dir='ltr'   >
   <body>
      <div class='pgSearch_layout'>
         <div class='pgSearch_layout_results'>
            <div class='pgSearch_layout_results_inner'>
               <div class='pgSearch_results'>
                  <ul class='searchResults'>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                           <h2 class='searchResultItem_title'>
                              <a href="https://data2.unhcr.org/en/documents/details/92127">
                              UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022
                              </a>
                           </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92127' data-title="UNHCR - Pakistan Ov 2022"
                                       title="Download"
                                       >
                                    <img src='https://data2.unhcr.org/bundles/common/img/icons/download-orange.svg' alt=''>
                                    Download
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92127"
                                       >
                                    View
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           <div class='searchResultItem_body'>
                              UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;19 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92127"
                                    href="https://data2.unhcr.org/en/documents/details/92127"
                                    data-visibility-toggle='#widget_6260e5417c608shareDialog_document_92127'>
                                 Share this page:
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417c608shareDialog_document_92127'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417c608shareDialog_document_92127'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 20 2022" data-share data-url='https://data2.unhcr.org/en/documents/details/92127'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92127'
                                             data-title='UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92127'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                           <h2 class='searchResultItem_title'>
                              <a target="_blank" href="https://data2.unhcr.org/en/documents/details/92134">
                              UNHCR Mozambique IDP Response External Update _February 2022
                              </a>
                           </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92134' data-title="UNHCR Mozambique IDP Response External Update _February 2022"
                                       title="Download"
                                       >
                                    Download
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92134"
                                       target="_blank"
                                       title="View"
                                       >
                                    View
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           <div class='searchResultItem_body'>
                              UNHCR Mozambique IDP Response External Update _February 2022
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;17 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92134"
                                    href="https://data2.unhcr.org/en/documents/details/92134"
                                    data-visibility-toggle='#widget_6260e5417c940shareDialog_document_92134'>
                                 Share this page:
                                 <i class='share_link_icon'></i>
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417c940shareDialog_document_92134'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417c940shareDialog_document_92134'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="UNHCR Mozambique IDP Response External Update _February 2022" data-summary="UNHCR Moza 2022" data-share data-url='https://data2.unhcr.org/en/documents/details/92134'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92134'
                                             data-title='UNHCR Mozambique IDP Response External Update _February 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92134'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                            <h2 class='searchResultItem_title'>
                                <a target="_blank" href="https://data2.unhcr.org/en/documents/details/92134">
                                Factsheet ProNexus March 2022
                                </a>
                            </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92148' data-title="Factsheet ProNexus March 2022"
                                       title="Download"
                                       >
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92148"
                                       >
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;11 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92148"
                                    href="https://data2.unhcr.org/en/documents/details/92148"
                                    data-visibility-toggle='#widget_6260e5417cd7bshareDialog_document_92148'>
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417cd7bshareDialog_document_92148'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417cd7bshareDialog_document_92148'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="Factsheet ProNexus March 2022" data-summary="" data-share data-url='https://data2.unhcr.org/en/documents/details/92148'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92148'
                                             data-title='Factsheet ProNexus March 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92148'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                     <li class='searchResultItem -document media -table'>
                        <div class='searchResultItem_content media_body'>
                           <h2 class='searchResultItem_title'>
                              <a target="_blank" href="https://data2.unhcr.org/en/documents/details/92125">
                              Myanmar UNHCR displacement overview 18 Apr 2022
                              </a>
                           </h2>
                           <span class='searchResultItem_type'>
                           document
                           </span>
                           <div class='searchResultItem_download'>
                              <ul class='inlineList -separated'>
                                 <li class='inlineList_item'>
                                    <a class='searchResultItem_download_link' href='https://data2.unhcr.org/en/documents/download/92125' data-title="Myanmar UNHCR displacement overview 18 Apr 2022"
                                       title="Download"
                                       >
                                    </a>
                                    <a class='searchResultItem_download_link'
                                       href="https://data2.unhcr.org/en/documents/details/92125"
                                       >
                                    View
                                    </a>
                                 </li>
                              </ul>
                           </div>
                           <div class='searchResultItem_body'>
                              Displacement Overview as of 18 Apr 2022
                           </div>
                           <span class='searchResultItem_date'>
                           Publish date: <b>20 April 2022</b> &#40;1 day ago&#41;
                           <br>
                           Create date: <b>20 April 2022</b> &#40;19 hours ago&#41;
                           </span>
                           <div class='searchResultItem_share'>
                              <div class='share'>
                                 <a class='share_link'
                                    data-fetch-share-url="https://data2.unhcr.org/en/documents/details/92125"
                                    href="https://data2.unhcr.org/en/documents/details/92125"
                                    data-visibility-toggle='#widget_6260e5417d135shareDialog_document_92125'>
                                 </a>
                                 <div class='share_dialog'
                                    id='widget_6260e5417d135shareDialog_document_92125'
                                    data-visibility-hideOnOutsideClick
                                    aria-hidden='true'>
                                    <a class='share_dialog_close' data-visibility-hide='#widget_6260e5417d135shareDialog_document_92125'>
                                    </a>
                                    <ul class='share_dialog_services inlineList'>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-facebook' data-title="Myanmar UNHCR displacement overview 18 Apr 2022" data-summary="Displacement Overview as of 18 Apr 2022" data-share data-url='https://data2.unhcr.org/en/documents/details/92125'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='' class='data-share-twitter' data-share data-url='https://data2.unhcr.org/en/documents/details/92125'
                                             data-title='Myanmar UNHCR displacement overview 18 Apr 2022'>
                                          </a>
                                       </li>
                                       <li class='inlineList_item'>
                                          <a href='mailto:?subject=Check out this document&body=Download here: https://data2.unhcr.org/en/documents/details/92125'>
                                          </a>
                                       </li>
                                    </ul>
                                 </div>
                              </div>
                           </div>
                        </div>
                     </li>
                  </ul>
               </div>
            </div>
         </div>
      </div>
   </body>
</html>
'''


UNHCR_WEB_MOCK_EXCEPTED_LEADS = [
    {
        "title": "UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022",
        "published_on": datetime.date(2022, 4, 20),
        "url": "https://data2.unhcr.org/en/documents/download/92127",
        "source_raw": "UNHCR Portal",
        "author_raw": "",
        "source_type": "",
    },
    {
        "title": "UNHCR Mozambique IDP Response External Update _February 2022",
        "published_on": datetime.date(2022, 4, 20),
        "url": "https://data2.unhcr.org/en/documents/download/92134",
        "source_raw": "UNHCR Portal",
        "author_raw": "",
        "source_type": "",
    },
    {
        "title": "Factsheet ProNexus March 2022",
        "published_on": datetime.date(2022, 4, 20),
        "url": "https://data2.unhcr.org/en/documents/download/92148",
        "source_raw": "UNHCR Portal",
        "author_raw": "",
        "source_type": "",
    },
    {
        "title": "UNHCR - Pakistan Overview of Refugee and Asylum-Seekers Population as of March 31, 2022",
        "published_on": datetime.date(2022, 4, 20),
        "url": "https://data2.unhcr.org/en/documents/download/92127",
        "source_raw": "UNHCR Portal",
        "author_raw": "",
        "source_type": "",
    },
    {
        "title": "UNHCR Mozambique IDP Response External Update _February 2022",
        "published_on": datetime.date(2022, 4, 20),
        "url": "https://data2.unhcr.org/en/documents/download/92134",
        "source_raw": "UNHCR Portal",
        "author_raw": "",
        "source_type": "",
    },
    {
        "title": "Factsheet ProNexus March 2022",
        "published_on": datetime.date(2022, 4, 20),
        "url": "https://data2.unhcr.org/en/documents/download/92148",
        "source_raw": "UNHCR Portal",
        "author_raw": "",
        "source_type": "",
    },
]
