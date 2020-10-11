function a = filterAnomaly(a0, start, hw, thres, mincount)
%This script takes a nupic anomaly signal (A), and reduces it to alert
%level signal by the following steps.
%1. ignore the first part specified by START (defautl is 1000).
%2. only consider signals that are larger than THRES (default is 0.1).
%3. alert is generated is the number of non-zero signals appear MINCOUNT
%(default is 3) times within HW (default is 50).

    if ~exist('start','var') || isempty(start)
        start = 1000;
    end
    if ~exist('hw','var') || isempty(hw)
        hw = 100;
    end
    if ~exist('thres','var') || isempty(thres)
        thres = 0.1;
    end
    if ~exist('mincount','var') || isempty(mincount)
        mincount = 3;
    end
    a = a0 > thres;
    a(1:start) = 0;
    for i=(start-hw):(length(a)-hw)
        if a(i) && sum(a((i-hw):(i+hw))) < mincount
            a(i) = 0;
        end
    end
    
            
    
    
    