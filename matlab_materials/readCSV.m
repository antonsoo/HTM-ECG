function X = readCSV(filename)
    X = xlsread(filename);
    X(find(isnan(X(:,1))),:)=[];
    
    