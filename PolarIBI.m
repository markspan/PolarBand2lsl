%% INPUT DATA:
data = load_xdf('sub-P001_ses-S001_task-Default_run-001_eeg_old7.xdf');
tm = data{1}.time_stamps-data{1}.time_stamps(1);
ecg = data{1}.time_series';
figure(1)
%% DETREND
[p,s,mu] = polyfit((1:numel(ecg))',ecg,6);
f_y = polyval(p,(1:numel(ecg))',[],mu);

ECG_data = ecg - f_y;        % Detrend data
ECG_data = ecg;
%% R-Top Trigger
plot(tm,ECG_data)
grid on
title('Detrended ECG Signal')
xlabel('Samples')
ylabel('Voltage(mV)')

[~,locs_Rwave] = findpeaks(ECG_data,'MinPeakHeight',400,...
                                    'MinPeakDistance',50);

%%  PLOT
hold on
t = tm(locs_Rwave);

plot(t,ECG_data(locs_Rwave),'ro')

ml = max(ylim);
nd = (ECG_data(locs_Rwave)*0) + ml;

plot(t,nd,'rv','MarkerFaceColor','r')
ibi = round(diff(tm(locs_Rwave)),3);
for i = 1:length(ibi)-1
    text((t(i)+t(i+1))/2,double(nd(i))-50,int2str(ibi(i)*1000), 'FontSize', 8, 'HorizontalAlignment', 'center')
end
hold off
legend('Detrended ECG Signal', 'R-Top')

figure(2)
histogram(ibi,40)
figure(3)
plot(ibi)