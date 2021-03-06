# -*- coding: utf-8 -*-
"""
Created on Fri May 19 11:19:28 2017

@author: qwang2
"""

import sys
import os
for x in os.walk('../'):
    sys.path.append(x[0])

import warnings
warnings.simplefilter('error',RuntimeWarning)

import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RationalQuadratic
from sklearn.gaussian_process.kernels import ExpSineSquared
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from scipy.spatial import KDTree
from scipy.stats.stats import pearsonr
from utilities import vol_utils

class spatial_extrapolation(vol_utils):    

    def __init__(self):
        self.logger = logging.getLogger('volume_project.spatial_extrapolation')
        super().__init__()
        self.rc_lookup = {201200:'Major Arterials', 201300:'Minor Arterials', 201400:'Collectors', 201500:'Locals'}
        self.time_var = {'aadt':'year', 'daily_profile_by_month':'year, month, hour', 'daily_total_by_month': 'year, month'}
        
    def average_neighbours(self, road_class, tablename):
        '''
        Fills in uncounted sites by averaging closest 5 (or less if there is not enough) neighbour volumes and upload to database
        '''
        if tablename == 'aadt':
            columns = ['group_number','dir_bin', 'year','neighbour_vol']
        if tablename == 'daily_total_by_month':
            columns = ['group_number','dir_bin', 'year','month','neighbour_vol']
        if tablename == 'daily_profile_by_month':
            columns = ['group_number','dir_bin', 'year','month','hour','neighbour_vol']    
            
        data = self.get_sql_results("query_avg_neighbour_volumes.sql",columns = columns, replace_columns = {'place_holder_table_name': tablename, 'place_holder_time_var': self.time_var[tablename]}, parameters = [road_class])
        data = [[None, a, 2015, b, c, 3] for a, b, c in zip(data['dir_bin'], data['neighbour_vol'], data['group_number'])]
        self.db.inserttable('prj_volume.'+tablename, data)
        self.logger.info('Uploaded results for road class ' + self.rc_lookup[road_class] + ' to prj_volume.' + tablename+ '. Estimated by averaging neighbour volumes')
        
    def average_neighbours_eval(self, road_class, sample_size, tablename):
        ''' 
        Evaluating results by averaging neighbour volumes by splitting available data into train and test set.
        '''
        
        if sample_size < 1:
            sample_size = sample_size*100
            
        if tablename == 'aadt':
            columns = ['group_number','dir_bin', 'year','neighbour_vol','volume']
        if tablename == 'daily_total_by_month':
            columns = ['group_number','dir_bin', 'year','month','neighbour_vol','volume']
        if tablename == 'daily_profile_by_month':
            columns = ['group_number','dir_bin', 'year','month','hour','neighbour_vol','volume']    
            
        data = self.get_sql_results("query_avg_neighbour_volumes_eval.sql",columns = columns, replace_columns = {'place_holder_table_name': tablename, 'place_holder_time_var': self.time_var[tablename]}, parameters = [road_class, sample_size])
        y_predict = data['neighbour_vol']
        y_test = data['volume']
        
        self.scatterplot(y_predict, y_test, road_class, r2_score(y_test, y_predict), 'neighbour_avg', ' Average of 5 Nearest Neighbours')
        self.logger.info('Average of Neighbour Volumes Evaluation for road class' + self.rc_lookup[road_class] + 'done.')
        
    def color_y_axis(self, ax, color):
        for t in ax.get_yticklabels():
            t.set_color(color)
           
    def fill_all(self, tablename):
        self.logger.info('Filling in Major Arterials')
        self.linear_regression_directional(201200, tablename)
        self.average_neighbours(201200, tablename)
        
        self.logger.info('Filling in Minor Arterials')
        self.linear_regression_directional(201300, tablename)
        self.average_neighbours(201300, tablename)
        
        self.logger.info('Filling in Collectors')
        self.average_neighbours(201400, tablename)
        
        self.logger.info('Filling in Locals')
        self.average_neighbours(201500, tablename)

    def get_coord_data(self, road_class, tablename):
        return self.get_sql_results("query_coord_volume.sql",['from_x','from_y','to_x','to_y','volume'], replace_columns = {'place_holder_table_name': tablename, 'place_holder_time_var': self.time_var[tablename]}, parameters=[road_class])

    def get_directional_rel_groups(self, road_class, tablename):
        '''
        Getting training data for linear regression by direction
        '''
        
        if tablename == 'aadt':
            columns = ['group_number','dir_bin', 'year','neighbour_vol','volume']
        if tablename == 'daily_total_by_month':
            columns = ['group_number','dir_bin', 'year','month','neighbour_vol','volume']
        if tablename == 'daily_profile_by_month':
            columns = ['group_number','dir_bin', 'year','month','hour','neighbour_vol','volume']
            
        return self.get_sql_results("query_relation_groups_train.sql",columns = columns, replace_columns = {'place_holder_table_name': tablename, 'place_holder_time_var': self.time_var[tablename]}, parameters = [road_class])
        
    def get_directional_rel_groups_test(self, road_class, tablename):
        '''
        Getting testing data for linear regression by direction
        '''
        if tablename == 'aadt':
            columns = ['group_number','dir_bin', 'year','neighbour_vol']
        if tablename == 'daily_total_by_month':
            columns = ['group_number','dir_bin', 'year','month','neighbour_vol']
        if tablename == 'daily_profile_by_month':
            columns = ['group_number','dir_bin', 'year','month','hour','neighbour_vol']
            
        return self.get_sql_results("query_relation_groups_test.sql",columns = columns, replace_columns = {'place_holder_table_name': tablename, 'place_holder_time_var': self.time_var[tablename]}, parameters = [road_class])
        
    def get_neighbour_data(self, road_class, nNeighbours, tablename):
        '''
        Getting neighbour volumes for linear regression by proximity.
        '''
        if tablename == 'aadt':
            columns = ['group_number','dir_bin', 'year','neighbour_vol']
        if tablename == 'daily_total_by_month':
            columns = ['group_number','dir_bin', 'year','month','neighbour_vol']
        if tablename == 'daily_profile_by_month':
            columns = ['group_number','dir_bin', 'year','month','hour','neighbour_vol']
            
        return self.get_sql_results("query_neighbour_volume.sql", columns = columns, replace_columns = {'place_holder_table_name': tablename, 'place_holder_time_var': self.time_var[tablename]}, parameters = [road_class, nNeighbours])
        
    def linear_regression_directional(self, road_class, tablename, sample_size = 1):
        ''' Directional linear regression.
        Doing evaluation if sample_size != 1, test_size = sample_size
        Estimating to fill in if sample_size = 1.
        '''
        
        if sample_size > 1:
            sample_size = sample_size / 100
            
        data = self.get_directional_rel_groups(road_class, tablename)
        self.logger.debug('Linear Regression Directional - Got Trainig Data')
        neighb = list(data[data['neighbour_vol'].map(len) == 4]['neighbour_vol'])
        orig = list(data[data['neighbour_vol'].map(len) == 4]['volume'])
        if sample_size != 1:
            x_train, x_test, y_train, y_test = train_test_split(neighb, orig, test_size=sample_size, random_state=0)
        else:
            x_train = neighb
            y_train = orig
        
        regr = linear_model.LinearRegression()
        regr.fit(x_train, y_train)
        self.logger.debug('Linear Regression Directional - Trained')
        if sample_size != 1:
            y_predict = regr.predict(x_test)
            self.scatterplot(y_predict, y_test, road_class, regr.score(x_test, y_test), 'directional_regr', ' Directional Linear Regression \n with 2 parallel and 2 perpendicular')
            self.logger.info('Directional Linear Regression Evaluation for road class' + self.rc_lookup[road_class] + 'done.')
        else:
            data = self.get_directional_rel_groups_test(road_class, tablename)
            data = data[data['neighbour_vol'].map(len) == 4]
            y_predict = regr.predict(list(data['neighbour_vol']))
            tabl = [[None, b, 2015, int(y), a, 2] for a,b,y in zip(data['group_number'], data['dir_bin'],y_predict)]
            self.db.inserttable('prj_volume.aadt', tabl)
            self.logger.info('Uploaded results for road class ' + self.rc_lookup[road_class] +' to prj_volume.aadt. Estimated by directional regression')
        return regr.coef_
        
    def linear_regression_prox(self, road_class, nNeighbours, tablename):
        '''
        AADT only.
        Estimate volume by regression by proximity and upload to database.
        '''
        
        data = self.get_coord_data(road_class, tablename)
        self.logger.debug('Linear Regression Proximity - Got Training Data')
        
        dist = np.array(data[['from_x','from_y','to_x','to_y']])
        kdt = KDTree(dist, nNeighbours + 1)
        orig = np.asarray([data['volume'].iloc[kdt.query(l,k=5)[1]].iloc[0] for l in dist])
        neighb = []
        for i in range(nNeighbours):
            neighb.append([data['volume'].iloc[kdt.query(l,k=11)[1]].iloc[i+1] for l in dist])
        neighb = np.asarray(neighb).T
        regr = linear_model.LinearRegression()
        regr.fit(neighb, orig)
        self.logger.debug('Linear Regression Proximity - Trained')       
        
        data = self.get_neighbour_data(road_class, nNeighbours, tablename)
        
        y_predict = regr.predict(list(data['neighbour_vol']))

        data = [[None, a, 2015, int(b), c, 4] for a, b, c in zip(data['dir_bin'],y_predict, data['group_number'])]
        
        self.db.inserttable('prj_volume.aadt', data)
        self.logger.info('Uploaded results for road class ' + self.rc_lookup[road_class] +' to prj_volume.aadt. Estimated by linear regression(proximity)')
        
        
    def linear_regression_prox_eval(self, road_class, sample_size=0.3):
        ''' AADT only
            This function evaluates linear regression by proximity on a given road class. **AADT only**
            Input:
                road_class: 6-digit feature code
                (optional) sample_size: the proportion of sample used for testing
            Output:
                (to screen)
                Scatter plot of predicted and observed value and the root mean squared error.
                Plot of root mean squred eroor vs. number of neighbours used for regression.
        '''
        data = self.get_coord_data(road_class).dropna()
        dist = np.array(data[['from_x','from_y','to_x','to_y']])
        kdt = KDTree(dist, 12)
        
        orig = np.asarray([data['volume'].iloc[kdt.query(l,k=5)[1]].iloc[0] for l in dist])
        neighb = []
        for i in range(10):
            neighb.append([data['volume'].iloc[kdt.query(l,k=11)[1]].iloc[i+1] for l in dist])
        neighb = np.asarray(neighb).T
        x_train, x_test, y_train, y_test = train_test_split(neighb, orig, test_size=sample_size, random_state=0)   
        regr = linear_model.LinearRegression()
        score = []
        for i in range(10):
            regr.fit(x_train[:,0:i+1], y_train)
            y_predict = regr.predict(x_test[:,0:i+1])
            if i == 9:
                self.scatterplot(y_predict, y_test, road_class, regr.score(x_test, y_test), 'proximity_regr',  ' Linear Regression (by proximity) \n with ' + str(i+2) + ' neighbours')
                new = np.insert(x_train[:,0:i+1], 0, 1, axis = 1)
                C = np.linalg.inv(np.matmul(new.transpose(),new)) * mean_squared_error(y_test,y_predict)/(len(new)-(i+2)-1)
                for j in range(i+1):
                    print(regr.coef_[j]/np.sqrt(C[j+1,j+1]))
                #print(mean_squared_error(y_test,y_predict)/(len(new)-(i+2)-1))
                    
            score.append(np.sqrt(mean_squared_error(y_test,y_predict)))
            
        fig, ax = plt.subplots(figsize=[8,6])    
        ax.plot(np.linspace(2, 11, 10), score)
        ax.set_title(self.rc_lookup[road_class] + ' Root Mean Squared Error')
        ax.set_xlabel('Number of Neighbour')
        ax.set_ylabel('Root Mean Squared Error (veh)')
        fig.savefig('spatial_extrapolation/img/'+self.rc_lookup[road_class].lower().replace(' ', '_') +'_proximity_regr_scores.png')
        
    def scatterplot(self, y_predict, y_test, road_class, coef_det, estimation_method, title_notes = ''):
        
        fig, ax = plt.subplots(figsize=[8,6])
        
        ax.scatter(y_predict, y_test)
        ax.set_title(self.rc_lookup[road_class] + title_notes)
        ax.set_xlabel('Predicted Volume (veh)')
        ax.set_ylabel('Observed Volume (veh)')
        x = np.linspace(0.8*min(min(y_test),min(y_predict)), 1.1*max(max(y_predict),max(y_test)),2)
        ax.plot(x,x)
        
        ax.set_xlim(x)
        ax.set_ylim(x)
        
        ax.annotate('Root Mean Squared Error: ' + "{:.0f}".format(np.sqrt(mean_squared_error(y_test,y_predict))), xy=((x[1]-x[0])*0.06+x[0], x[1]*0.92), fontsize = 11)
        ax.annotate('Coef of Det: ' + "{:.3f}".format(coef_det), xy=((x[1]-x[0])*0.06+x[0], x[1]*0.86), fontsize = 11)
        try:
            fig.savefig('spatial_extrapolation/img/'+self.rc_lookup[road_class].lower().replace(' ','_') + '_' + estimation_method + '.png')
        except FileNotFoundError:
            fig.savefig(self.rc_lookup[road_class].lower().replace(' ','_') + '_' + estimation_method + '.png')
            
    def plot_semivariogram(self, road_class):
        data = self.get_sql_results("query_semi_variogram.sql", columns = ['dist','semivariance','correlation','numobs'], parameters=[road_class])
        data['dist'] = data['dist']*50/1000
        fig, ax = plt.subplots(figsize=[8,6])
        ax1 = ax.twinx()
        ax2 = ax.twinx()
        ax.plot(data['dist'], data['semivariance'], color='b', label='semivariance')
        ax1.plot(data['dist'], data['correlation'], 'r')
        ax2.plot(data['dist'], data['numobs'], 'c', label='Num Observations')
        ax.set_xlabel('Distance (km)')
        h0, l0 = ax.get_legend_handles_labels()
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h0+h1+h2, l0+l1+l2)
        self.color_y_axis(ax,'b')
        self.color_y_axis(ax1,'r')
        self.color_y_axis(ax2,'c')
        ax.set_title(self.rc_lookup[road_class]+' Semivariogram')
        fig.savefig('spatial_extrapolation/img/'+self.rc_lookup[road_class].lower().replace(' ', '_') +'_semivariogram.png')
        
    # Back up function
    def Kriging(self, road_class):    
        group = self.get_sql_results("query_coord_volume.sql", columns = ['from_x','from_y','to_x','to_y','volume'], parameters=[road_class])
    
        volume = np.array(group['volume'])
        coord = np.array(group[['from_x','from_y','to_x','to_y']])
        
        coord = preprocessing.normalize(coord, axis=0)
        x_train, x_test, y_train, y_test = train_test_split(coord, volume, test_size=0.3, random_state=0)
    
        kernel =  RationalQuadratic()
        gp = GaussianProcessRegressor(kernel=kernel)
        gp.fit(x_train, y_train)
        
        y_predict = gp.predict(x_test, return_std=False)
        self.scatterplot(y_predict, y_test, road_class, 0, 'Kriging', '')