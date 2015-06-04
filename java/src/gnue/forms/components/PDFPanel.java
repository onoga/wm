/*
 * $Id: PDFPanel.java,v 1.2 2009/09/02 14:35:16 oleg Exp $
 *
 * Copyright 2004 Sun Microsystems, Inc., 4150 Network Circle,
 * Santa Clara, California 95054, U.S.A. All rights reserved.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */
package gnue.forms.components;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Image;
import java.awt.Rectangle;
import java.awt.image.ImageObserver;
import java.awt.event.MouseListener;
import java.awt.event.MouseEvent;

import javax.swing.JPanel;

import com.sun.pdfview.*;

/**
 * A Swing-based panel that displays a PDF page image.  If the zoom tool
 * is in use, allows the user to select a particular region of the image to
 * be zoomed.
 */
public class PDFPanel extends JPanel implements ImageObserver, MouseListener {

	/** The image of the rendered PDF page being displayed */
	Image image;
	/** The current PDFPage that was rendered into image */
	PDFPage page;
	/** The horizontal offset of the image from the left edge of the panel */
	int offx;
	/** The vertical offset of the image from the top of the panel */
	int offy;
	/** the size of the image */
	Dimension size;

	/** a flag indicating whether the current page is done or not. */
	Flag flag = new Flag();

	/**
	 * Create a new PDFPanel, with a default size of 800 by 600 pixels.
	 */
	public PDFPanel() {
		super();
		setPreferredSize(new Dimension(800, 600));
		setFocusable(true);
		addMouseListener(this);
		//addMouseMotionListener(this);
   }

	/**
	 * Stop the generation of any previous page, and draw the new one.
	 * @param page the PDFPage to draw.
	 */
	public synchronized void showPage(PDFPage page) {
		// stop drawing the previous page
		if (page != null && size != null) {
			page.stop(size.width, size.height, null);
		}

		// set up the new page
		this.page = page;

		if (page == null) {
			// no page
			image = null;
			repaint();
		} else {
			// start drawing -- clear the flag to indicate we're in progress.
			flag.clear();
			//ystem.out.println("   flag cleared");

			// image should fit preferred size
			// image should fit size if panel is smaller than preferred size
			int width  = Math.min(getPreferredSize().width,  getSize().width );
			int height = Math.min(getPreferredSize().height, getSize().height);

			if (width + height > 0) {

				//ystem.out.println("Ratios: scrn="+((float)sz.width/sz.height)+
				//				   ", clip="+(clip==null ? 0 : clip.getWidth()/clip.getHeight()));

				this.size = page.getUnstretchedSize(width, height, null);

				// get the new image
				this.image = page.getImage(size.width, size.height, null, this);

				repaint();
			}
		}
	}

	public void setPreferredSize(Dimension size) {
		if (super.getPreferredSize() != size) {
			super.setPreferredSize(size);
			this.image = null;
			this.size = null;
			repaint();
		}
	}

	//public void revalidate

	public Dimension getPreferredSize() {
		return size == null ? super.getPreferredSize() : this.size;
	}


	/**
	 * Draw the image.
	 */
	public void paint(Graphics g) {
		Dimension sz = getSize();
		g.setColor(getBackground());
		g.fillRect(0, 0, getWidth(), getHeight());
		if (image == null) {
			if (page == null) {
				// No image -- draw an empty box
				// [[MW: remove the scary red X]]
				//		g.setColor(Color.red);
				//		g.drawLine(0, 0, getWidth(), getHeight());
				//		g.drawLine(0, getHeight(), getWidth(), 0);
				g.setColor(Color.black);
				g.drawString("No page selected", getWidth() / 2 - 30, getHeight() / 2);
			}
			else {
				// image not generated yet, pr invalidated
				showPage(page);
			}
		} else {
			// draw the image
			int imageWidth  = image.getWidth (null);
			int imageHeight = image.getHeight(null);

			if (imageWidth <= sz.width && imageHeight <= sz.height) {
				// draw it centered within the panel
				this.offx = (sz.width  - imageWidth ) / 2;
				this.offy = (sz.height - imageHeight) / 2;
				g.drawImage(image, offx, offy, this);

			} else {
				// the image size is wrong.  try again, or give up.
				if (page != null) {
					showPage(page);
				}
			}
		}
	}

	/**
	 * Gets the page currently being displayed
	 */
	public PDFPage getPage() {
		return page;
	}

	/**
	 * Gets the size of the image currently being displayed
	 */
	public Dimension getCurSize() {
		return size;
	}

	/**
	 * Waits until the page is either complete or had an error.
	 */
	public void waitForCurrentPage() {
		flag.waitForFlag();
	}

	/**
	 * Handles notification of the fact that some part of the image
	 * changed.  Repaints that portion.
	 * @return true if more updates are desired.
	 */
	public boolean imageUpdate(Image img, int infoflags, int x, int y, int width, int height) {
		//ystem.out.println("Image update: " + (infoflags & ALLBITS));
		Dimension sz = getSize();
		if ((infoflags & (SOMEBITS | ALLBITS)) != 0) {
			// [[MW: dink this rectangle by 1 to handle antialias issues]]
			repaint(x + offx, y + offy, width, height);
		}
		if ((infoflags & (ALLBITS | ERROR | ABORT)) != 0) {
			flag.set();
			//ystem.out.println("   flag set");
			return false;
		} else {
			return true;
		}
	}

	public void mouseClicked(MouseEvent e) {
		requestFocus();
	}
	public void mouseEntered(MouseEvent e) {}
	public void mouseExited(MouseEvent e) {}
	public void mousePressed(MouseEvent e) {}
	public void mouseReleased(MouseEvent e) {}

}
