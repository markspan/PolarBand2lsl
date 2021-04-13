%% INPUT DATA:
data = load_xdf('longerdata.xdf');
tmOrig = data{1}.time_stamps-data{1}.time_stamps(1);
ecg = data{1}.time_series';

% part:
ecg = ecg(tmOrig>1000 & tmOrig<1250);
tmOrig = tmOrig(tmOrig>1000 & tmOrig<1250);

figure(100);
[RoonIbi,~,~] = getIBI(ecg,tmOrig);

figure(1)
%% DETREND
[p,s,mu] = polyfit((1:numel(ecg))',ecg,6);
f_y = polyval(p,(1:numel(ecg))',[],mu);

ECG_data = ecg - f_y;        % Detrend data
plot(tmOrig,ECG_data, 'k-')

%% RESAMPLE USING CUBIC SPLINE METHOD
% 'new' time axis
tm = tmOrig(1):.001:tmOrig(end);
% cubic spline interpolationj
ECG_data = spline(tmOrig,ECG_data,tm);
%ECG_data = ecg;              % or keep it RAW
%% Plot the ECG trace data
hold on
plot(tm,ECG_data)
grid on
title('Detrended ECG Signal')
xlabel('Samples')
ylabel('Voltage(mV)')
%% R-Top Trigger
[~,locs_Rwave] = findpeaks(ECG_data,'MinPeakHeight',400,...
                                    'MinPeakDistance',50);
disp(['found '  int2str(length(locs_Rwave))  ' r-tops'])



%%  PLOT the Triggered R-tops
hold on
t = tm(locs_Rwave);
plot(t,ECG_data(locs_Rwave),'ro')

ml = max(ylim);
nd = (ECG_data(locs_Rwave)*0) + ml;

plot(t,nd,'rv','MarkerFaceColor','r')
%% Plot the IBI values
ibi = round(diff(tm(locs_Rwave)),3);
for i = 1:length(ibi)-1
    text((t(i)+t(i+1))/2,double(nd(i))-50,int2str(ibi(i)*1000), 'FontSize', 8, 'HorizontalAlignment', 'center')
end
hold off
legend('Detrended ECG Signal', 'R-Top')
%% Plot ibi values histogram
figure(2)
histogram(ibi,40)
%% plot the IBI values over time
figure(3)
plot(ibi)
figure(4)
plot(ibi-RoonIbi)