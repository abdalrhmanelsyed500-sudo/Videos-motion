import cv2, sys
src, out, y0, y1, x0, x1, z = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:8])
im = cv2.imread(src)[y0:y1, x0:x1]; im = cv2.resize(im, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
for y in range((y0 // 20 + 1) * 20, y1, 20):
    yy = (y - y0) * z; cv2.line(im, (0, yy), (im.shape[1], yy), (255, 255, 0) if y % 100 == 0 else (120, 120, 0), 1)
    if y % 100 == 0 or True: cv2.putText(im, str(y), (2, yy - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
for x in range((x0 // 20 + 1) * 20, x1, 20):
    xx = (x - x0) * z; cv2.line(im, (xx, 0), (xx, im.shape[0]), (255, 255, 0) if x % 100 == 0 else (120, 120, 0), 1)
    cv2.putText(im, str(x), (xx + 2, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
cv2.imwrite(out, im)
