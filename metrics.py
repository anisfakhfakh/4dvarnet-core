import datetime
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import pandas as pd
import shapely
from shapely import wkt
#import geopandas as gpd
from cartopy import crs as ccrs
import cartopy.feature as cfeature
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cv2
import matplotlib.animation as animation

from spectral import *

def plot_snr(gt,oi,pred,resfile):
    '''
    gt: 3d numpy array (Ground Truth)
    oi: 3d numpy array (OI)
    pred: 3d numpy array (4DVarNet-based predictions)
    resfile: string
    '''

    dt = pred.shape[1]

    # Compute Signal-to-Noise ratio
    f, pf = avg_err_rapsd2dv1(oi,gt,4.,True)
    wf = 1./f
    snr_oi = [wf, pf]
    f, pf = avg_err_rapsd2dv1(pred,gt,4.,True)
    wf = 1./f
    snr_pred = [wf, pf]

    # plot Signal-to-Noise ratio
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(snr_oi[0],snr_oi[1],color='red',linewidth=2,label='OI')
    ax.plot(snr_pred[0],snr_pred[1],color='blue',linewidth=2,label='4DVarNet')
    ax.set_xlabel("Wavenumber", fontweight='bold')
    ax.set_ylabel("Signal-to-noise ratio", fontweight='bold')
    ax.set_xscale('log') ; ax.set_yscale('log')
    plt.legend(loc='best',prop=dict(size='small'),frameon=False)
    plt.xticks([50, 100, 200, 500, 1000], ["50km", "100km", "200km", "500km", "1000km"])
    ax.invert_xaxis()
    plt.grid(which='both', linestyle='--')
    plt.savefig(resfile) # save the figure
    fig = plt.gcf()
    plt.close()          # close the figure
    return fig


def plot_nrmse(gt, oi, pred, resfile, time):
    '''
    gt: 3d numpy array (Ground Truth)
    oi: 3d numpy array (OI)
    pred: 3d numpy array (4DVarNet-based predictions)
    resfile: string
    time: 1d array-like of time corresponding to the experiment
    '''

    # Compute daily nRMSE scores
    nrmse_oi = []
    nrmse_pred = []
    for i in range(len(oi)):
        nrmse_oi.append(nrmse(gt[i], oi[i]))
        nrmse_pred.append(nrmse(gt[i], pred[i]))

    # plot nRMSE time series
    plt.plot(range(len(oi)),nrmse_oi,color='red',
                 linewidth=2,label='OI')
    plt.plot(range(len(pred)),nrmse_pred,color='blue',
                 linewidth=2,label='4DVarNet')

    # graphical options
    plt.ylabel('nRMSE')
    plt.xlabel('Time (days)')
    plt.xticks(range(0,len(gt)),time,rotation=45, ha='right')
    plt.margins(x=0)
    plt.grid(True,alpha=.3)
    plt.legend(loc='upper left',prop=dict(size='small'),frameon=False,bbox_to_anchor=(0,1.02,1,0.2),ncol=2,mode="expand")
    plt.savefig(resfile,bbox_inches="tight")    # save the figure
    fig = plt.gcf()
    plt.close()                                 # close the figure
    return  fig

def plot_mse(gt, oi, pred, resfile, time):
    '''
    gt: 3d numpy array (Ground Truth)
    oi: 3d numpy array (OI)
    pred: 3d numpy array (4DVarNet-based predictions)
    resfile: string
    time: 1d array-like of time corresponding to the experiment
    '''

    # Compute daily nRMSE scores
    mse_oi = []
    mse_pred = []
    grad_mse_oi = []
    grad_mse_pred = []
    for i in range(len(oi)):
        mse_oi.append(mse(gt[i], oi[i]))
        mse_pred.append(mse(gt[i], pred[i]))
        grad_mse_oi.append(mse(gradient(gt[i],2), gradient(oi[i],2)))
        grad_mse_pred.append(mse(gradient(gt[i],2), gradient(pred[i],2)))
    print("mse_oi = ", np.nanmean(mse_oi))
    print("mse_pred = ", np.nanmean(mse_pred))
    print("grad_mse_oi = ", np.nanmean(grad_mse_oi))
    print("grad_mse_pred = ", np.nanmean(grad_mse_pred))
    print("percentage_ssh = ", np.abs(np.nanmean(mse_oi)-np.nanmean(mse_pred))/np.nanmean(mse_oi))
    print("percentage_ssh_grad = ", np.abs(np.nanmean(grad_mse_oi)-np.nanmean(grad_mse_pred))/np.nanmean(grad_mse_oi))

    # plot nRMSE time series
    plt.plot(range(len(oi)),mse_oi,color='red',
                 linewidth=2,label='OI')
    plt.plot(range(len(pred)),mse_pred,color='blue',
                 linewidth=2,label='4DVarNet')

    # graphical options
    plt.ylabel('MSE')
    plt.xlabel('Time (days)')
    plt.xticks(range(0,len(gt)),time,rotation=45, ha='right')
    plt.margins(x=0)
    plt.grid(True,alpha=.3)
    plt.legend(loc='upper left',prop=dict(size='small'),frameon=False,bbox_to_anchor=(0,1.02,1,0.2),ncol=2,mode="expand")
    plt.savefig(resfile,bbox_inches="tight")    # save the figure
    fig = plt.gcf()
    plt.close()                                 # close the figure
    return  fig

def plot(ax,lon,lat,data,title,extent=[-65,-55,30,40],cmap="coolwarm",gridded=True,vmin=-2,vmax=2,colorbar=True,orientation="horizontal"):
    ax.set_extent(list(extent))
    if gridded:
        im=ax.pcolormesh(lon, lat, data, cmap=cmap,\
                          vmin=vmin, vmax=vmax,edgecolors='face', alpha=1, \
                          transform= ccrs.PlateCarree(central_longitude=0.0))
    else:
        im=ax.scatter(lon, lat, c=data, cmap=cmap, s=1,\
                       vmin=vmin, vmax=vmax,edgecolors='face', alpha=1, \
                       transform= ccrs.PlateCarree(central_longitude=0.0))
    im.set_clim(vmin,vmax)
    if colorbar==True:
        clb = plt.colorbar(im, orientation=orientation, extend='both', pad=0.1, ax=ax)
    ax.set_title(title, pad=40, fontsize = 15)
    gl = ax.gridlines(alpha=0.5,draw_labels=True)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabels_bottom = False
    gl.ylabels_right = False
    gl.xlabel_style = {'fontsize': 10, 'rotation' : 45}
    gl.ylabel_style = {'fontsize': 10}
    # ax[i][j].coastlines(resolution='50m')

def gradient(img, order):
    """ calcuate x, y gradient and magnitude """
    sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=3)
    sobelx = sobelx/8.0
    sobely = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=3)
    sobely = sobely/8.0
    sobel_norm = np.sqrt(sobelx*sobelx+sobely*sobely)
    if (order==0):
        return sobelx
    elif (order==1):
        return sobely
    else:
        return sobel_norm

def plot_maps(gt,obs,oi,pred,lon,lat,resfile,grad=False):

    if grad==False:
        vmax = np.nanmax(np.abs(oi))
        vmin = -1.*vmax
    else:
        vmax = np.nanmax(np.abs(gradient(oi,2)))
        vmin = 0

    extent = [np.min(lon),np.max(lon),np.min(lat),np.max(lat)]

    id_nan = np.where(np.isnan(gt))
    obs[id_nan] = np.nan

    fig = plt.figure(figsize=(15,15))
    ax1 = fig.add_subplot(221, projection=ccrs.PlateCarree(central_longitude=0.0))
    ax2 = fig.add_subplot(222, projection=ccrs.PlateCarree(central_longitude=0.0))
    ax3 = fig.add_subplot(223, projection=ccrs.PlateCarree(central_longitude=0.0))
    ax4 = fig.add_subplot(224, projection=ccrs.PlateCarree(central_longitude=0.0))

    if grad==False:
        plot(ax1,lon,lat,gt,'GT',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
        plot(ax2,lon,lat,obs,'OBS',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
        plot(ax3,lon,lat,oi,'OI',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
        plot(ax4,lon,lat,pred,'4DVarNet',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
    else:
        plot(ax1,lon,lat,gradient(gt,2),r"$\nabla_{GT}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
        plot(ax2,lon,lat,gradient(obs,2),r"$\nabla_{OBS}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
        plot(ax3,lon,lat,gradient(oi,2),r"$\nabla_{OI}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
        plot(ax4,lon,lat,gradient(pred,2),r"$\nabla_{4DVarNet}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
  
    plt.savefig(resfile)    # save the figure
    fig = plt.gcf()
    plt.close()             # close the figure
    return fig


def animate_maps(gt,obs,oi,pred,lon,lat,resfile,orthographic=True,dw=4,grad=False):

    if dw>1:
        # decrease the resolution
        Nlon = len(lon)
        Nlat = len(lat)
        ilon = np.arange(0,Nlon,4)
        ilat = np.arange(0,Nlat,4)
        gt = (gt[:,ilat,:])[:,:,ilon]
        obs = (obs[:,ilat,:])[:,:,ilon]
        oi = (oi[:,ilat,:])[:,:,ilon]
        pred = (pred[:,ilat,:])[:,:,ilon]
        lon = lon[ilon]
        lat = lat[ilat]

    def animate(i):
        print(i)
        id_nan = np.where(np.isnan(gt[i]))
        obs[i][id_nan] = np.nan
        #oi[i][id_nan] = np.nan
        #pred[i][id_nan] = np.nan

        if grad==False:
            plot(ax1,lon,lat,gt[i],'GT',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
            plot(ax2,lon,lat,obs[i],'OBS',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
            plot(ax3,lon,lat,oi[i],'OI',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
            plot(ax4,lon,lat,pred[i],'4DVarNet',extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
        else:
            plot(ax1,lon,lat,gradient(gt[i],2),r"$\nabla_{GT}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
            plot(ax2,lon,lat,gradient(obs[i],2),r"$\nabla_{OBS}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
            plot(ax3,lon,lat,gradient(oi[i],2),r"$\nabla_{OI}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)
            plot(ax4,lon,lat,gradient(pred[i],2),r"$\nabla_{4DVarNet}$",extent=extent,cmap="viridis",vmin=vmin,vmax=vmax)

    if grad==False:
        vmax = np.nanmax(np.abs(oi))
        vmin = -1.*vmax
    else:
        vmax = np.nanmax(np.abs(gradient(oi,2)))
        vmin = 0

    extent = [np.min(lon),np.max(lon),np.min(lat),np.max(lat)]

    fig = plt.figure(figsize=(15,15))
    if orthographic==False:
        ax1 = fig.add_subplot(221, projection=ccrs.PlateCarree(central_longitude=0.0))
        ax2 = fig.add_subplot(222, projection=ccrs.PlateCarree(central_longitude=0.0))
        ax3 = fig.add_subplot(223, projection=ccrs.PlateCarree(central_longitude=0.0))
        ax4 = fig.add_subplot(224, projection=ccrs.PlateCarree(central_longitude=0.0))
    else:
        ax1 = fig.add_subplot(221, projection=ccrs.Orthographic(-30, 45))
        ax2 = fig.add_subplot(222, projection=ccrs.Orthographic(-30, 45))
        ax3 = fig.add_subplot(223, projection=ccrs.Orthographic(-30, 45))
        ax4 = fig.add_subplot(224, projection=ccrs.Orthographic(-30, 45))
    plt.subplots_adjust(hspace=0.5)
    ani = animation.FuncAnimation(fig, animate, frames=len(gt), interval=200, repeat=False)
    writergif = animation.PillowWriter(fps=3) 
    writer = animation.FFMpegWriter(fps=3)
    ani.save(resfile, writer = writer)
    plt.close()

def plot_ensemble(pred,lon,lat,resfile):

    vmax = np.nanmax(np.abs(pred))
    vmin = -1.*vmax
    grad_vmax = np.nanmax(np.abs(gradient(pred,2)))
    grad_vmin = 0
    extent = [np.min(lon),np.max(lon),np.min(lat),np.max(lat)]

    n_members = pred.shape[-1]
    fig, ax = plt.subplots(2,n_members,figsize=(5*n_members,15),squeeze=False,
                          subplot_kw=dict(projection=ccrs.PlateCarree(central_longitude=0.0)))
    for i in range(n_members):
        plot(ax,0,i,lon,lat,pred[:,:,i],'M'+str(i),extent=extent,cmap="coolwarm",vmin=vmin,vmax=vmax)
        plot(ax,1,i,lon,lat,gradient(pred[:,:,i],2),r"$\nabla_{M"+str(i)+"}$",extent=extent,cmap="viridis",vmin=grad_vmin,vmax=grad_vmax)
    plt.savefig(resfile)       # save the figure
    plt.close()                # close the figure

def save_netcdf(saved_path1, pred, lon, lat, time,
                time_units='days since 2012-10-01 00:00:00'):
    '''
    saved_path1: string 
    pred: 3d numpy array (4DVarNet-based predictions)
    lon: 1d numpy array 
    lat: 1d numpy array
    time: 1d array-like of time corresponding to the experiment
    '''

    mesh_lat, mesh_lon = np.meshgrid(lat, lon)
    mesh_lat = mesh_lat.T
    mesh_lon = mesh_lon.T

    dt = pred.shape[1]
    xrdata = xr.Dataset( \
        data_vars={'longitude': (('lat', 'lon'), mesh_lon), \
                   'latitude': (('lat', 'lon'), mesh_lat), \
                   'Time': (('time'), time), \
                   'ssh': (('time', 'lat', 'lon'), pred[:, int(dt / 2), :, :])}, \
        coords={'lon': lon, 'lat': lat, 'time': np.arange(len(pred))})
    xrdata.time.attrs['units'] = time_units
    xrdata.to_netcdf(path=saved_path1, mode='w')


def nrmse(ref, pred):
    '''
    ref: Ground Truth fields
    pred: interpolated fields
    '''
    return np.sqrt(np.nanmean(((ref - np.nanmean(ref)) - (pred - np.nanmean(pred))) ** 2)) / np.nanstd(ref)


def nrmse_scores(gt, oi, pred, resfile):
    '''
    gt: 3d numpy array (Ground Truth)
    oi: 3d numpy array (OI)
    pred: 3d numpy array (4DVarNet-based predictions)
    resfile: string
    '''
    # Compute daily nRMSE scores
    nrmse_oi = []
    nrmse_pred = []
    for i in range(len(oi)):
        nrmse_oi.append(nrmse(gt[i], oi[i]))
        nrmse_pred.append(nrmse(gt[i], pred[i]))
    tab_scores = np.zeros((2, 3))
    tab_scores[0, 0] = np.nanmean(nrmse_oi)
    tab_scores[0, 1] = np.percentile(nrmse_oi, 5)
    tab_scores[0, 2] = np.percentile(nrmse_oi, 95)
    tab_scores[1, 0] = np.nanmean(nrmse_pred)
    tab_scores[1, 1] = np.percentile(nrmse_pred, 5)
    tab_scores[1, 2] = np.percentile(nrmse_pred, 95)
    np.savetxt(fname=resfile, X=tab_scores, fmt='%2.2f')
    return tab_scores

def mse(ref, pred):
    '''
    ref: Ground Truth fields
    pred: interpolated fields
    '''
    return np.nanmean(((ref-np.nanmean(ref))-(pred-np.nanmean(pred)))**2)


def mse_scores(gt, oi, pred, resfile):
    '''
    gt: 3d numpy array (Ground Truth)
    oi: 3d numpy array (OI)
    pred: 3d numpy array (4DVarNet-based predictions)
    resfile: string
    '''
    # Compute daily nRMSE scores
    mse_oi = []
    mse_pred = []
    for i in range(len(oi)):
        mse_oi.append(mse(gt[i], oi[i]))
        mse_pred.append(mse(gt[i], pred[i]))
    tab_scores = np.zeros((2, 3))
    tab_scores[0, 0] = np.nanmean(mse_oi)
    tab_scores[0, 1] = np.percentile(mse_oi, 5)
    tab_scores[0, 2] = np.percentile(mse_oi, 95)
    tab_scores[1, 0] = np.nanmean(mse_pred)
    tab_scores[1, 1] = np.percentile(mse_pred, 5)
    tab_scores[1, 2] = np.percentile(mse_pred, 95)
    np.savetxt(fname=resfile, X=tab_scores, fmt='%2.2f')



def compute_metrics(x_test, x_rec):
    # MSE
    mse = np.mean((x_test - x_rec) ** 2)

    # MSE for gradient
    gx_rec = np.gradient(x_rec, axis=[1, 2])
    gx_rec = np.sqrt(gx_rec[0] ** 2 + gx_rec[1] ** 2)

    gx_test = np.gradient(x_test, axis=[1, 2])
    gx_test = np.sqrt(gx_test[0] ** 2 + gx_test[1] ** 2)

    gmse = np.mean((gx_test - gx_rec) ** 2)
    ng = np.mean((gx_rec) ** 2)

    return {'mse': mse, 'mseGrad': gmse, 'meanGrad': ng}
