function plotError(X, i, j, k)
    if ~exist('i','var') | isempty(i)
        i=1;
    end
    if ~exist('j','var') | isempty(j)
        j=2;
    end
    if ~exist('k','var') | isempty(k)
        k=[];
        np = 3;
    else
        np = 5;
    end
%     i=2; j=2;
    subplot(np,1,1);
    plot(X(:,i));
    title('input');
    a = axis();
    subplot(np,1,2);
    plot(X(:,j));
    title('predicttion');
    axis(a);
    subplot(np,1,3);
    err = (X(:,i)-X(:,j))./abs(X(:,i));
%     err = filterError(err, 3);
    plot(err);
%     plot((X(:,i)-X(:,j))./abs(X(:,i)));
%     plot(X(:,3));
    axis([a(1) a(2) -1 1]);
    title('error');
    if np==5
        subplot(np, 1, 4);
        plot(X(:,k));
        axis([a(1) a(2) 0 1]);
        title('anomaly');
        subplot(np, 1, 5);
        af = filterAnomaly(X(:,k), 6000);
        plot(af);
        axis([a(1) a(2) 0 1]);
        title('anomaly filtered');
    end
    
function err = filterError(err, w) 
%     im = repmat(abs(err), [1 3]);
%     j = imregionalmin(im, 4);
%     k = imregionalmax(im, 4);
%     err(j(:,2)==0 | k(:,2)==0) = 0;
    aerr = abs(err);
    for i=(w+1):length(err)-w
        val = median(aerr((i-w):(i+w)));
        if val ~= abs(err(i))
            err(i) = 0;
        end
    end
    
    