/*
 * Copyright © 2017 Orange, Inc. and others.  All rights reserved.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v1.0 which accompanies this distribution,
 * and is available at http://www.eclipse.org/legal/epl-v10.html
 */

package org.opendaylight.transportpce.common.fixedflex;

public final class FixedFlexImpl implements FixedFlexInterface {
    private long index;
    private double centerFrequency;
    private double start;
    private double stop;
    private double wavelength;
    // wavelengthSpacing is in GHz
    double wavelengthSpacing = 100.0;
    // endFrequency is in THz
    final double endFrequency = 196.0;
    // java double is double float - d or D is appended to treat it explicitly as double float
    final double precision = 100d;

    public FixedFlexImpl(Long index, double centreFrequency, double start, double stop, double wavelength) {
        this.index = index;
        this.centerFrequency = centreFrequency;
        this.start = start;
        this.stop = stop;
        this.wavelength = wavelength;
    }

    public FixedFlexImpl() {
        this.index = 0L;
        this.centerFrequency = 0;
        this.start = 0;
        this.stop = 0;
        this.wavelength = 0;
    }

    public FixedFlexImpl(long wlIndex) {
        this.index = wlIndex;
        this.centerFrequency = endFrequency - (wlIndex - 1) * wavelengthSpacing / 1000;
        this.wavelength = (299792458 / this.centerFrequency) / 1000;
        // Truncate the value to the two decimal places
        this.centerFrequency = Math.round(this.centerFrequency * precision) / precision;
        this.start = this.centerFrequency - (wavelengthSpacing / 2) / 1000;
        this.start = Math.round(this.start * precision) / precision;
        this.stop = this.centerFrequency + (wavelengthSpacing / 2) / 1000;
        this.stop = Math.round(this.stop * precision) / precision;
        this.wavelength = Math.round(this.wavelength * precision) / precision;
    }

    @Override
    /**
     * @param index Wavelength number
     * @return Returns FixedFlexImp object with the calculated result.
     **/
    public FixedFlexImpl getFixedFlexWaveMapping(long wlIndex) {
        FixedFlexImpl fixedFlex = new FixedFlexImpl();
        fixedFlex.centerFrequency = endFrequency - (wlIndex - 1) * wavelengthSpacing / 1000;
        fixedFlex.centerFrequency = Math.round(fixedFlex.centerFrequency * precision) / precision;
        fixedFlex.wavelength = (299792458 / fixedFlex.centerFrequency) / 1000;
        fixedFlex.wavelength = Math.round(fixedFlex.wavelength * precision) / precision;
        fixedFlex.start = fixedFlex.centerFrequency - (wavelengthSpacing / 2) / 1000;
        fixedFlex.start = Math.round(fixedFlex.start * precision) / precision;
        fixedFlex.stop = fixedFlex.centerFrequency + (wavelengthSpacing / 2) / 1000;
        fixedFlex.stop = Math.round(fixedFlex.stop * precision) / precision;
        fixedFlex.index = wlIndex;
        return fixedFlex;
    }

    public double getCenterFrequency() {
        return centerFrequency;
    }

    public double getStart() {
        return start;
    }

    public long getIndex() {
        return index;
    }

    public double getStop() {
        return stop;
    }

    public double getWavelength() {
        return wavelength;
    }
}
