function [ibis, par, t] = getIBI(ecgData, ecgTimestamps, varargin)
%  GETIBI Detects the IBI values from a ECG trace. Using interpolation to get ms. precision
% 
% Algorithm developed by A.M. van Roon for PRECAR (CARSPAN preprocessing).
% 
% Matlab version M.M.Span (2021)

%%  default values:
par.fSample = -1;
par.MinPeakHeight = median(ecgData)+(2*std(ecgData));
par.MinPeakDistance = 350; %ms!
par.deTrend = true;
par.Plot = true;

%% Parse the name - value pairs found in varargin
%------------------------------------------------------------------------------------------
for arg = 1:2:length(varargin)
    % is the name a parameter?
    if isfield(par,varargin{arg})
        % and does it have a value?
        if length(varargin)<=arg
            ME = MException('getIBI:MissingValue', ...
                'Parameter %s should be followed by a value',varargin{arg});
            throw(ME)
        end
        par.(varargin{arg}) = varargin{arg+1};
    else
        ME = MException('getIBI:noSuchParameter', ...
            'Parameter %s does not exist',varargin{arg});
        throw(ME)
    end
end
%% ------------------------------------------------------------------------------------------
% if no sampleRate is given, calculatie it from the samples and the
% timestamps
if (par.fSample == -1)
    duration = ecgTimestamps(end)-ecgTimestamps(1);
    par.fSample = round(1.0/(duration / length(ecgTimestamps)));
end
%% convert MinPeakDistance from ms to samples
par.MinPeakDistance = (par.MinPeakDistance/1000.0)*par.fSample;
%% ------------------------------------------------------------------------------------------
% are we asked to detrend the data? Detrend algorithm in this file (below).
if (par.deTrend)
   ecgData = deTrend(ecgData);
end


%% Then, first find the (approximate) peaks
[~,locs] = findpeaks(ecgData,'MinPeakHeight',par.MinPeakHeight,...
    'MinPeakDistance',par.MinPeakDistance);
vals = ecgData(locs);
disp(['*found '  int2str(length(vals))  ' r-tops'])
%% Now the algorithm can start.
%------------------------------------------------------------------------------------------
rc = max(abs(vals - ecgData(locs - 1)), abs(ecgData(locs + 1) - vals));
try
    correction =  (ecgData(locs + 1) - ecgData(locs - 1)) / par.fSample / 2 ./ abs(rc);
catch ME
    causeException = MException('MATLAB:getIBI:divisionbyzero', 'rc is zero at some point in the data');
    ME = addCause(ME,causeException);
    rethrow(ME);
end
RTopTime = ecgTimestamps(locs) + correction';
ibis = round(diff(RTopTime),3);
if (par.Plot) % Plot algorithm in this file (below)
    PlotECGWithIBIS(ecgTimestamps,ecgData,locs,RTopTime)
end
end
%%
function ecgData = deTrend(ecgData)
    [p,~,mu] = polyfit((1:numel(ecgData))',ecgData,6);
    f_y = polyval(p,(1:numel(ecgData))',[],mu);
    ecgData = ecgData - f_y;        % Detrend data
end
%%
function PlotECGWithIBIS(ecgTimestamps,ecgData,locs,rtops)
    %% Plot the ECG trace data
    ibis = round(diff(rtops),3);
    hold on
    plot(ecgTimestamps,ecgData)
    xlim([ecgTimestamps(1) min(ecgTimestamps(1)+10,ecgTimestamps(end))]);
    grid on
    title('(Detrended) ECG Signal (mV)')
    xlabel('time (sec)')
    ylabel('Voltage(mV)')
    
    %%  PLOT the Triggered R-tops
    hold on
    plot(rtops,ecgData(locs),'ro')
    
    %% also plot thim at the top of ther plot:
    ml = max(ylim);
    nd = (ecgData(locs)*0) + ml;
    plot(rtops,nd,'rv','MarkerFaceColor','r')
    
    %% Plot the IBI value labels in between the top r-top markers:
    for i = 1:length(ibis)-1
        text(double(rtops(i)+rtops(i+1))/2,double(nd(i))-50,int2str(ibis(i)*1000), 'FontSize', 8, 'HorizontalAlignment', 'center')
    end
    hold off
    legend('Detrended ECG Signal', 'R-Top')    
end