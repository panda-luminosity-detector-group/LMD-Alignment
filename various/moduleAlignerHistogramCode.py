if histDat:
                #! begin hist
                import matplotlib
                import matplotlib.pyplot as plt
                from matplotlib.colors import LogNorm
                
                # plot difference hit array
                fig = plt.figure(figsize=(9/2.54, 9/2.54))
                
                axis = fig.add_subplot(1,1,1)
                axis.hist2d(newTracks[:, 1, 0]*1e4, newTracks[:, 1, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-300,300), (-300,300)))
                axis.set_title(f'track px vs py')
                axis.yaxis.tick_left()
                axis.set_xlabel('px [µm]')
                axis.set_ylabel('py [µm]')
                axis.tick_params(direction='out')
                axis.yaxis.set_label_position("left")

                # axis2 = fig.add_subplot(1,2,2)
                # axis2.hist(newTracks[:, 1, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
                # axis2.set_title(f'pz')
                # axis2.yaxis.tick_right()
                # axis2.set_xlabel('pz [µm]')
                # axis2.set_ylabel('count')
                # axis2.yaxis.set_label_position("right")

                fig.tight_layout()
                fig.savefig(f'output/alignmentModules/test/trackDirections/sec{sector}-it{iIteration}.png')
                plt.close(fig)
                #! end hist

if histDat:

                    #! begin hist
                    # dVec = pIntersection - recoPosArr

                    fig = plt.figure(figsize=(16/2.54, 9/2.54))
                    axis2 = fig.add_subplot(1,2,1)
                    axis2.hist2d(dVec[:, 0]*1e4, dVec[:, 1]*1e4, bins=50, norm=LogNorm(), label='Count (log)')#, range=((-300,300), (-300,300)))
                    axis2.set_title(f'track/reco dx vs dy')
                    axis2.yaxis.tick_left()
                    axis2.set_xlabel('dx [µm]')
                    axis2.set_ylabel('dy [µm]')
                    axis2.tick_params(direction='out')
                    axis2.yaxis.set_label_position("left")

                    axis3 = fig.add_subplot(1,2,2)
                    axis3.hist(dVec[:, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
                    axis3.set_title(f'dz')
                    axis3.yaxis.tick_right()
                    axis3.set_xlabel('dz [µm]')
                    axis3.set_ylabel('count')
                    axis3.yaxis.set_label_position("right")

                    fig.tight_layout()
                    fig.savefig(f'output/alignmentModules/test/trackDirections/sec{sector}-it{iIteration}-plane{i}.png')
                    plt.close(fig)

                    #! end hist