Introduction
============

This module installs a menuitem 'Download attachments' in the Action menu of an expense report.
Pressing this buttons results in the collective download of all attachments in one pdf file, to disk, that will be opened in the browser.

This module work on Odoo V16.


Installation
============

Prerequisites

* sudo apt update && sudo apt install img2pdf && sudo apt install imagemagick
  * $ img2pdf -V --> img2pdf 0.4.2
  * $ convert -version  -->  ImageMagick 6.9.11-60
  
* pip3 install PyPDF2==1.26.0
* pip3 install reportlab==3.5.13

+ pip requirements https://github.com/marcothedood/ODOO-CUSTOM-ADDONS-download_attachments/blob/16.0/requirements.txt

Module installation


Usage
=====

We've added support for different imgs formats.

* jpeg
* png
* jpg

PDF and URL are working too.

When one of the attachments is of an unsupported type, a Validation error is raised.

If for some reason the conversion to pdf and the merging of pdf pages to the overall pdf fails,
another Validation error is raised.

In both cases the filename of the attachment that is the cause of the error, is specified.

urls are converted to hyperlinks, that can be clicked inside a box.
The expense name is displayed as a title above this box.

We do not store any expense report in the database or in the filestore.
Thank to the controller, files are streamed to the browser directly instead of being cached locally on the srv.
